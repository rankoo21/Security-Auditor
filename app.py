"""
Auditor - Powered by OpenGradient SDK
"""
import os, json, threading, time, hashlib, re

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import opengradient as og
from web3 import Web3

app = Flask(__name__, static_folder="static")
CORS(app)

PRIVATE_KEY = os.environ.get("OG_PRIVATE_KEY") or ""
if PRIVATE_KEY:
    PRIVATE_KEY = PRIVATE_KEY.strip()
    if not PRIVATE_KEY.startswith("0x") and len(PRIVATE_KEY) == 64:
        PRIVATE_KEY = "0x" + PRIVATE_KEY

w3b   = Web3(Web3.HTTPProvider("https://sepolia.base.org"))

def safe_wallet():
    try:
        acct = w3b.eth.account.from_key(PRIVATE_KEY)
        return acct.address
    except:
        return "0x00...00"

WALLET = safe_wallet()

OPG_TOKEN = Web3.to_checksum_address("0x240b09731D96979f50B2C649C9CE10FcF9C7987F")
ERC20_ABI = [
    {"inputs":[{"name":"account","type":"address"}],"name":"balanceOf",
     "outputs":[{"name":"","type":"uint256"}],"stateMutability":"view","type":"function"},
    {"inputs":[],"name":"decimals",
     "outputs":[{"name":"","type":"uint8"}],"stateMutability":"view","type":"function"},
]
token = w3b.eth.contract(address=OPG_TOKEN, abi=ERC20_ABI)

def get_opg_balance():
    try:
        raw = token.functions.balanceOf(WALLET).call()
        dec = token.functions.decimals().call()
        return round(raw / 10**dec, 4)
    except Exception as e:
        return 0.0

# Set Active Model
ACTIVE_MODEL = og.TEE_LLM.GEMINI_2_0_FLASH
ACTIVE_MODEL_NAME = "GEMINI_2_0_FLASH"

# Initialize client (lazy, no approval on startup for Vercel)
_client = None
def get_client():
    global _client
    if _client is None and PRIVATE_KEY:
        try:
            _client = og.Client(private_key=PRIVATE_KEY)
        except Exception as e:
            print(f"Client init error: {e}")
    return _client

# ── Audit system prompt (English) ───────────────────────────────────
AUDIT_SYSTEM_PROMPT = """You are an expert Solidity auditor. Analyze the provided code for security vulnerabilities.
You MUST respond with valid JSON ONLY. No markdown, no code fences, no extra text.

JSON Structure:
{
  "summary": "1-2 sentences assessment in English",
  "risk_score": 0,
  "vulnerabilities": [
    {
      "id": "V-001",
      "title": "Vulnerability Name",
      "severity": "critical|high|medium|low",
      "description": "Detailed description of the vulnerability",
      "line_hint": "Affected line",
      "recommendation": "Recommendation to fix it",
      "cwe": "CWE-XXX"
    }
  ],
  "gas_optimizations": [
    {"title": "Title", "description": "Description", "estimated_savings": "low|medium|high"}
  ],
  "best_practices": [
    {"title": "Practice", "status": "pass|fail", "note": "Note"}
  ]
}

Keep descriptions concise (max 2 sentences each). Max 5 vulnerabilities.
All text and descriptions MUST be in English."""

# Store audit history in memory
audit_history = []

def repair_json(s):
    """Robust helper to close truncated JSON strings/objects using state machine."""
    s = s.strip()
    if not s:
        return "{}"

    in_string = False
    escape = False
    stack = []

    for char in s:
        if escape:
            escape = False
            continue
        if char == '\\':
            escape = True
            continue
        if char == '"':
            in_string = not in_string
            continue

        if not in_string:
            if char == '{':
                stack.append('}')
            elif char == '[':
                stack.append(']')
            elif char == '}':
                if stack and stack[-1] == '}':
                    stack.pop()
            elif char == ']':
                if stack and stack[-1] == ']':
                    stack.pop()

    # Close unterminated string
    if in_string:
        if s.endswith('\\'):
            s = s[:-1]
        s += '"'

    # Close remaining brackets/braces in correct order
    while stack:
        s += stack.pop()

    return s

@app.after_request
def cors_headers(r):
    r.headers["Access-Control-Allow-Origin"]  = "*"
    r.headers["Access-Control-Allow-Headers"] = "Content-Type"
    r.headers["Access-Control-Allow-Methods"] = "GET,POST,OPTIONS"
    return r

@app.route("/")
def index():
    return send_from_directory("static", "index.html")

@app.route("/api/status")
def status():
    return jsonify({
        "wallet": WALLET,
        "balance": get_opg_balance(),
        "model": ACTIVE_MODEL_NAME,
        "total_audits": len(audit_history)
    })

@app.route("/api/audit", methods=["POST","OPTIONS"])
def audit():
    if request.method == "OPTIONS":
        return jsonify({}), 200

    data = request.get_json(force=True) or {}
    code = data.get("code", "").strip()

    if not code:
        return jsonify({"success": False, "error": "No code provided"}), 400

    if len(code) > 50000:
        return jsonify({"success": False, "error": "Code too long (max 50,000 chars)"}), 400

    client = get_client()
    if not client:
        return jsonify({"success": False, "error": "SDK not initialized. Check OG_PRIVATE_KEY."}), 500

    # Generate code hash for reference
    code_hash = hashlib.sha256(code.encode()).hexdigest()[:16]
    audit_id  = f"AUDIT-{code_hash}-{int(time.time())}"

    messages = [
        {"role": "system", "content": AUDIT_SYSTEM_PROMPT},
        {"role": "user",   "content": f"Audit this Solidity contract:\n\n{code}"}
    ]

    try:
        result = client.llm.chat(
            model=ACTIVE_MODEL,
            messages=messages,
            max_tokens=1000,
            temperature=0.1,
            x402_settlement_mode=og.x402SettlementMode.SETTLE_BATCH
        )

        raw   = (result.chat_output or {}).get("content", "") or ""
        phash = getattr(result, "payment_hash", None)

        # Parse JSON from response - with robust extraction
        s = raw.strip()

        # Remove markdown code fences if present
        if "```json" in s:
            s = s.split("```json")[1].split("```")[0]
        elif "```" in s:
            parts = s.split("```")
            if len(parts) > 1:
                s = parts[1]
                if s.startswith("json"):
                    s = s[4:]

        s = s.strip()

        # Try normal parsing first
        parsed = None
        try:
            parsed = json.loads(s)
        except json.JSONDecodeError:
            # Try repairing truncated JSON
            try:
                repaired = repair_json(s)
                parsed = json.loads(repaired)
            except:
                # Try regex extraction as last resort
                match = re.search(r'(\{.*)', s, re.DOTALL)
                if match:
                    try:
                        repaired2 = repair_json(match.group(1))
                        parsed = json.loads(repaired2)
                    except Exception as e2:
                        parsed = {
                            "summary": "AI response was truncated. Partial analysis available.",
                            "risk_score": 50,
                            "vulnerabilities": [],
                            "gas_optimizations": [],
                            "best_practices": [],
                            "raw_response": raw[:500]
                        }
                else:
                    parsed = {
                        "summary": "Could not parse AI response.",
                        "risk_score": 50,
                        "vulnerabilities": [],
                        "gas_optimizations": [],
                        "best_practices": [],
                        "raw_response": raw[:500]
                    }

        # Add metadata
        parsed["audit_id"]     = audit_id
        parsed["code_hash"]    = code_hash
        parsed["payment_hash"] = phash
        parsed["model"]        = ACTIVE_MODEL_NAME
        parsed["timestamp"]    = int(time.time())
        parsed["code_length"]  = len(code)

        # Count severities
        sevs = {"critical":0, "high":0, "medium":0, "low":0, "info":0}
        for v in parsed.get("vulnerabilities", []):
            sev = v.get("severity", "info").lower()
            sevs[sev] = sevs.get(sev, 0) + 1
        parsed["severity_counts"] = sevs

        # Store in history
        audit_history.append({
            "audit_id": audit_id,
            "code_hash": code_hash,
            "timestamp": parsed["timestamp"],
            "risk_score": parsed.get("risk_score", 0),
            "summary": parsed.get("summary", ""),
            "severity_counts": sevs
        })

        return jsonify({"success": True, "audit": parsed})

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/api/history")
def history():
    return jsonify({"audits": list(reversed(audit_history[-20:]))})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(debug=False, host="0.0.0.0", port=port)
