"""
Auditor - Powered by OpenGradient SDK
"""
import os, json, threading, time, hashlib

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

PRIVATE_KEY = os.environ.get("OG_PRIVATE_KEY") or "PASTE_YOUR_KEY_HERE"
w3b   = Web3(Web3.HTTPProvider("https://sepolia.base.org"))
acct  = w3b.eth.account.from_key(PRIVATE_KEY)
WALLET = acct.address

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
        return f"error({e})"

def run_in_thread(fn, timeout=120):
    """Run callable in a fresh thread (fixes Windows asyncio conflicts)."""
    result_box = [None]
    error_box  = [None]
    def run():
        try: result_box[0] = fn()
        except Exception as e: error_box[0] = e
    t = threading.Thread(target=run)
    t.start()
    t.join(timeout=timeout)
    if t.is_alive(): raise Exception(f"Timed out after {timeout}s")
    if error_box[0]: raise error_box[0]
    return result_box[0]

# ── Startup ─────────────────────────────────────────────────────────
print(f"\n{'='*60}")
print(f"  * Smart Contract Auditor - OpenGradient SDK")
print(f"{'='*60}")
print(f"  SDK version    : {og.__version__ if hasattr(og,'__version__') else 'unknown'}")
print(f"  Wallet         : {WALLET}")
print(f"  OPG balance    : {get_opg_balance()}")

client = og.Client(private_key=PRIVATE_KEY)

print(f"\n  Running ensure_opg_approval...")
try:
    approval = client.llm.ensure_opg_approval(opg_amount=5.0)
    print(f"  Before : {approval.allowance_before/1e18:.4f} OPG")
    print(f"  After  : {approval.allowance_after/1e18:.4f} OPG")
    print(f"  Tx     : {approval.tx_hash or 'none (already approved)'}")
    print(f"  (OK) Permit2 approved")
except AttributeError:
    print(f"  (X) ensure_opg_approval not found - run: pip install opengradient --upgrade")
except Exception as e:
    print(f"  (X) Error: {e}")

# Set Active Model to Gemini 2.0 Flash which was most stable in testing
ACTIVE_MODEL = og.TEE_LLM.GEMINI_2_0_FLASH
ACTIVE_MODEL_NAME = "GEMINI_2_0_FLASH"

print(f"\n  Active model : {ACTIVE_MODEL_NAME}")
print(f"  Open: http://localhost:5000")
print(f"{'='*60}\n")

# ── Audit system prompt (English) ───────────────────────────────────
AUDIT_SYSTEM_PROMPT = """You are an expert Solidity auditor. Analyze the provided code for security vulnerabilities.
You MUST respond with valid JSON ONLY. No markdown.

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

All text and descriptions MUST be in English."""

# Store audit history in memory
audit_history = []

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

    # Generate code hash for reference
    code_hash = hashlib.sha256(code.encode()).hexdigest()[:16]
    audit_id  = f"AUDIT-{code_hash}-{int(time.time())}"

    print(f"\n[AUDIT] {audit_id} | {len(code)} chars | model: {ACTIVE_MODEL_NAME}", flush=True)

    messages = [
        {"role": "system", "content": AUDIT_SYSTEM_PROMPT},
        {"role": "user",   "content": f"Audit this Solidity contract:\n\n```solidity\n{code}\n```"}
    ]

    # Logging only ASCII info for Windows compatibility
    print(f"[DEBUG] messages sent: {len(messages)}", flush=True)
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
        print(f"[AUDIT] <- Response: {len(raw)} chars | tx:{phash}", flush=True)

        # Parse JSON from response
        try:
            s = raw.strip()
            if "```" in s:
                parts = s.split("```")
                if len(parts) > 1:
                    s = parts[1]
                    if s.startswith("json"): s = s[4:]
            parsed = json.loads(s.strip())
        except Exception as parse_err:
            print(f"[AUDIT] JSON parse error: {parse_err}", flush=True)
            parsed = {
                "summary": "Error parsing AI response",
                "risk_score": 50,
                "vulnerabilities": [],
                "gas_optimizations": [],
                "best_practices": [],
                "raw_response": raw
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
            "risk_score": parsed["risk_score"],
            "summary": parsed["summary"],
            "severity_counts": sevs
        })

        return jsonify({"success": True, "audit": parsed})

    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"[AUDIT] SDK/API Error: {e}", flush=True)
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/api/history")
def history():
    return jsonify({"audits": list(reversed(audit_history[-20:]))})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(debug=False, host="0.0.0.0", port=port)
