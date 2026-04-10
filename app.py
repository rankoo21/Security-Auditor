"""
Auditor - Powered by OpenGradient SDK 0.9.3
Uses direct IP (3.15.214.21) natively bypassing SSL checks.
"""
import os, json, threading, time, hashlib, re
import asyncio
try:
    import nest_asyncio
    nest_asyncio.apply()
except ImportError:
    pass

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

try:
    from flask import Flask, request, jsonify, send_from_directory
    from flask_cors import CORS
except Exception as e:
    print(f"[BOOT] Flask import failed: {e}")

try:
    import opengradient as og
    print(f"[BOOT] opengradient version: {getattr(og, '__version__', 'unknown')}")
except Exception as e:
    print(f"[BOOT] opengradient import failed: {e}")

try:
    from web3 import Web3
except Exception as e:
    print(f"[BOOT] web3 import failed: {e}")

app = Flask(__name__, static_folder="static")
CORS(app)

PRIVATE_KEY = os.environ.get("OG_PRIVATE_KEY") or ""
if PRIVATE_KEY:
    PRIVATE_KEY = PRIVATE_KEY.strip()
    if not PRIVATE_KEY.startswith("0x") and len(PRIVATE_KEY) == 64:
        PRIVATE_KEY = "0x" + PRIVATE_KEY

# OpenGradient 0.9.4 handles gateway discovery automatically.

w3b = Web3(Web3.HTTPProvider("https://sepolia.base.org"))

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
    except:
        return 0.0

def _m(name, fallback=None):
    """Safely get a TEE_LLM enum member by name."""
    val = getattr(og.TEE_LLM, name, None)
    if val is not None:
        return val
    if fallback:
        # If fallback is provided, let's just attempt it
        fallback_val = getattr(og.TEE_LLM, fallback, None)
        if fallback_val:
            return fallback_val
    return getattr(og.TEE_LLM, "GEMINI_2_5_FLASH", None)

MODELS = {
    # Legacy keys
    "GEMINI_2_0_FLASH":      _m("GEMINI_2_5_FLASH"),
    "GEMINI_1_5_FLASH":      _m("GEMINI_1_5_FLASH",      "GEMINI_2_5_FLASH"),
    "GPT_4O":                _m("GPT_4_1_2025_04_14",    "GEMINI_2_5_FLASH"),
    "GPT_4_1_2025_04_14":    _m("GPT_4_1_2025_04_14",    "GEMINI_2_5_FLASH"),
    "CLAUDE_3_7_SONNET":     _m("CLAUDE_SONNET_4_5",     "GEMINI_2_5_FLASH"),
    # Front-end dropdown values
    "GEMINI_2_5_FLASH":      _m("GEMINI_2_5_FLASH",      "GEMINI_2_5_FLASH"),
    "GEMINI_2_5_PRO":        _m("GEMINI_2_5_PRO",        "GEMINI_2_5_FLASH"),
    "GEMINI_3_FLASH":        _m("GEMINI_3_FLASH",        "GEMINI_2_5_FLASH"),
    "GPT_5_MINI":            _m("GPT_5_MINI",            "GPT_4_1_2025_04_14"),
    "GPT_5":                 _m("GPT_5",                 "GPT_4_1_2025_04_14"),
    "O4_MINI":               _m("O4_MINI",               "GPT_4_1_2025_04_14"),
    "GEMINI_2_5_FLASH_LITE": _m("GEMINI_2_5_FLASH_LITE", "GEMINI_2_5_FLASH"),
    "CLAUDE_HAIKU_4_5":      _m("CLAUDE_HAIKU_4_5",      "GEMINI_2_5_FLASH"),
    "CLAUDE_SONNET_4_5":     _m("CLAUDE_SONNET_4_5",     "GEMINI_2_5_FLASH"),
    "CLAUDE_SONNET_4_6":     _m("CLAUDE_SONNET_4_6",     "GEMINI_2_5_FLASH"),
    "GROK_4_FAST":           _m("GROK_4_FAST",           "GEMINI_2_5_FLASH"),
}

ACTIVE_MODEL = _m("GEMINI_2_5_FLASH_LITE")
ACTIVE_MODEL_NAME = "GEMINI_2_5_FLASH_LITE"

def make_llm():
    """Create og.LLM for 0.9.3"""
    if not PRIVATE_KEY:
        return None
    try:
        # OpenGradient 0.9.4 discovery
        llm = og.LLM(private_key=PRIVATE_KEY)
        return llm
    except Exception as e:
        print(f"[LLM] Init error: {e}")
        return None

# ── System prompt ──
AUDIT_SYSTEM_PROMPT = """You are a senior smart contract security auditor.
Your goal is to provide accurate, stable, and deterministic vulnerability analysis for Solidity contracts.
You MUST respond with valid JSON ONLY. No markdown, no code fences, no extra text.

STRICT RULES:

1) DO NOT hallucinate vulnerabilities.
   - Only report issues that are clearly exploitable.
   - If uncertain, mark as "Needs Manual Review".

2) VERSION AWARENESS:
   - If Solidity >=0.8.0:
     - Do NOT report overflow/underflow
     - Do NOT recommend SafeMath

3) REENTRANCY:
   - Only report if:
     - External call exists AND
     - State update happens AFTER the call
   - If CEI pattern is respected, explicitly say SAFE

4) ACCESS CONTROL:
   - Only flag functions that:
     - Modify ownership
     - Transfer funds
     - Change critical state
   - Ignore harmless public functions

5) DO NOT FLAG:
   - require(success) as redundant
   - Gas optimizations as vulnerabilities

6) SEVERITY RULES:
   - critical = Direct fund drain or full contract takeover
   - high = Strong exploit affecting funds or control
   - medium = Logic flaw or indirect exploit
   - low = Best practices (events, style)
   - info = Gas or suggestions

7) ALWAYS INCLUDE:
   - "No critical vulnerabilities found" in summary if none exist

JSON Structure:
{
  "summary": "Professional assessment. State 'No critical vulnerabilities found' if none exist.",
  "risk_score": 0,
  "vulnerabilities": [
    {
      "id": "V-001",
      "title": "Vulnerability Name",
      "severity": "critical|high|medium|low|info",
      "description": "Technical explanation with exploit scenario",
      "line_hint": "Affected line or function",
      "recommendation": "Specific fix recommendation",
      "cwe": "CWE-XXX"
    }
  ],
  "gas_optimizations": [
    {"title": "Title", "description": "Description", "estimated_savings": "low|medium|high"}
  ],
  "best_practices": [
    {"title": "Practice", "status": "pass|fail|safe", "note": "Note"}
  ]
}

CRITICAL OUTPUT RULES:
- Keep response concise (max 800 tokens).
- Use valid JSON ONLY.
- NEVER change the output structure.
- Keep consistent formatting across responses.
- Response in English."""

# ── Re-evaluation prompt (second pass) ──
REVIEW_SYSTEM_PROMPT = """You are a senior smart contract security auditor performing a SECOND-PASS REVIEW.
You MUST respond with valid JSON ONLY. No markdown, no code fences, no extra text.

You are given a previous audit report (as JSON) and the original Solidity source code.
Your job is to RE-EVALUATE the report and fix any errors:

CHECK FOR:
1) FALSE POSITIVES: Remove any vulnerability that is not clearly exploitable.
2) INCORRECT SEVERITY: Downgrade or upgrade severity based on these strict rules:
   - critical = Direct fund drain or full contract takeover ONLY
   - high = Strong exploit affecting funds or control
   - medium = Logic flaw or indirect exploit
   - low = Best practices (events, style)
   - info = Gas or suggestions
3) SOLIDITY VERSION VIOLATIONS:
   - If pragma >= 0.8.0: REMOVE any overflow/underflow findings. REMOVE SafeMath recommendations.
4) INCORRECT CLASSIFICATION:
   - If CEI (Checks-Effects-Interactions) pattern is followed, reentrancy is SAFE, remove it
   - require(success) is NOT redundant, do not flag it
   - Gas optimizations are NOT vulnerabilities, move to gas_optimizations section
5) RISK SCORE: Recalculate based on ACTUAL remaining vulnerabilities only.
   - 0 = No issues, 1-25 = Low, 26-50 = Medium, 51-75 = High, 76-100 = Critical

Return the CORRECTED JSON in the exact same structure. Keep valid entries unchanged.
If no vulnerabilities remain, set risk_score to 0 and summary must include 'No critical vulnerabilities found'."""

audit_history = []

def repair_json(s):
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
            if char == '{': stack.append('}')
            elif char == '[': stack.append(']')
            elif char == '}':
                if stack and stack[-1] == '}': stack.pop()
            elif char == ']':
                if stack and stack[-1] == ']': stack.pop()
    if in_string:
        if s.endswith('\\'): s = s[:-1]
        s += '"'
    while stack:
        s += stack.pop()
    return s

def parse_llm_json(raw):
    s = raw.strip()
    if "```json" in s:
        s = s.split("```json")[1].split("```")[0]
    elif "```" in s:
        parts = s.split("```")
        if len(parts) > 1:
            s = parts[1]
            if s.startswith("json"): s = s[4:]
    s = s.strip()
    try:
        return json.loads(s)
    except:
        pass
    try:
        return json.loads(repair_json(s))
    except:
        pass
    match = re.search(r'(\{.*)', s, re.DOTALL)
    if match:
        try:
            return json.loads(repair_json(match.group(1)))
        except:
            pass
    return None

# ── Flask routes ──

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

llm_lock = threading.Lock()
MAX_RETRIES = 3
RETRY_DELAY = 1

@app.route("/api/audit", methods=["POST","OPTIONS"])
def audit():
    if request.method == "OPTIONS":
        return jsonify({}), 200

    data = request.get_json(force=True) or {}
    code = data.get("code", "").strip()
    req_model = data.get("model", "GEMINI_2_5_FLASH")

    if not code:
        return jsonify({"success": False, "error": "No code provided"}), 400

    target_model = MODELS.get(req_model, ACTIVE_MODEL)
    target_model_name = req_model if req_model in MODELS else ACTIVE_MODEL_NAME

    code_hash = hashlib.sha256(code.encode()).hexdigest()[:16]
    audit_id  = f"AUDIT-{code_hash}-{int(time.time())}"

    messages = [
        {"role": "system", "content": AUDIT_SYSTEM_PROMPT},
        {"role": "user",   "content": f"Audit this Solidity contract:\n\n{code}"}
    ]

    last_error = None
    parsed = None
    phash = None

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            llm = make_llm()
            if not llm:
                return jsonify({"success": False, "error": "SDK not initialized. Check OG_PRIVATE_KEY."}), 500

            print(f"[Audit] Attempt {attempt}/{MAX_RETRIES} with {target_model_name}...")

            with llm_lock:
                try:
                    loop = asyncio.get_event_loop()
                    if loop.is_closed():
                        loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(loop)
                    result = loop.run_until_complete(llm.chat(
                        model=target_model,
                        messages=messages,
                        max_tokens=1000,
                        temperature=0.0,
                        x402_settlement_mode=og.x402SettlementMode.BATCH_HASHED
                    ))
                except RuntimeError:
                    result = asyncio.run(llm.chat(
                        model=target_model,
                        messages=messages,
                        max_tokens=1000,
                        temperature=0.0,
                        x402_settlement_mode=og.x402SettlementMode.BATCH_HASHED
                    ))

            # Safely extract response text in 0.9.3
            raw_output = getattr(result, "chat_output", None)
            if isinstance(raw_output, dict):
                raw = raw_output.get("content", "")
            elif hasattr(raw_output, "content"):
                raw = getattr(raw_output, "content")
            else:
                raw = str(raw_output) or ""
                
            phash = getattr(result, "payment_hash", None)
            parsed = parse_llm_json(raw)

            if parsed:
                print(f"[Audit] Attempt {attempt} SUCCESS!")
                break
            else:
                print(f"[Audit] Attempt {attempt}: got response but JSON parse failed")
                last_error = "LLM response could not be parsed as JSON: " + str(raw)[:50]

        except Exception as e:
            last_error = str(e)
            print(f"[Audit] Attempt {attempt} error: {last_error}")

        if attempt < MAX_RETRIES:
            delay = RETRY_DELAY * attempt
            print(f"[Audit] Waiting {delay}s before retry...")
            time.sleep(delay)

    # ── Second pass: Re-evaluation ──
    if parsed:
        try:
            print(f"[Audit] Running re-evaluation pass...")
            review_messages = [
                {"role": "system", "content": REVIEW_SYSTEM_PROMPT},
                {"role": "user", "content": f"Original Solidity code:\n\n{code}\n\nPrevious audit report:\n\n{json.dumps(parsed, indent=2)}\n\nRe-evaluate and return corrected JSON."}
            ]

            llm = make_llm()
            if llm:
                with llm_lock:
                    try:
                        loop = asyncio.get_event_loop()
                        if loop.is_closed():
                            loop = asyncio.new_event_loop()
                            asyncio.set_event_loop(loop)
                        review_result = loop.run_until_complete(llm.chat(
                            model=target_model,
                            messages=review_messages,
                            max_tokens=1000,
                            temperature=0.0,
                            x402_settlement_mode=og.x402SettlementMode.BATCH_HASHED
                        ))
                    except RuntimeError:
                        review_result = asyncio.run(llm.chat(
                            model=target_model,
                            messages=review_messages,
                            max_tokens=1000,
                            temperature=0.0,
                            x402_settlement_mode=og.x402SettlementMode.BATCH_HASHED
                        ))

                review_output = getattr(review_result, "chat_output", None)
                if isinstance(review_output, dict):
                    review_raw = review_output.get("content", "")
                elif hasattr(review_output, "content"):
                    review_raw = getattr(review_output, "content")
                else:
                    review_raw = str(review_output) or ""

                review_parsed = parse_llm_json(review_raw)
                if review_parsed:
                    print(f"[Audit] Re-evaluation SUCCESS — using corrected report")
                    parsed = review_parsed
                else:
                    print(f"[Audit] Re-evaluation JSON parse failed — keeping original")
        except Exception as e:
            print(f"[Audit] Re-evaluation error (keeping original): {e}")

    # Build response
    try:
        if parsed is None:
            if last_error:
                return jsonify({"success": False, "error": last_error}), 500
            parsed = {
                "summary": "AI response was truncated. Please try again.",
                "risk_score": 50,
                "vulnerabilities": [],
                "gas_optimizations": [],
                "best_practices": [],
            }

        parsed["audit_id"]     = audit_id
        parsed["code_hash"]    = code_hash
        parsed["payment_hash"] = phash
        parsed["model"]        = target_model_name
        parsed["timestamp"]    = int(time.time())
        parsed["code_length"]  = len(code)

        sevs = {"critical":0, "high":0, "medium":0, "low":0, "info":0}
        for v in parsed.get("vulnerabilities", []):
            sev = v.get("severity", "info").lower()
            sevs[sev] = sevs.get(sev, 0) + 1
        parsed["severity_counts"] = sevs

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

@app.route("/api/debug")
def debug():
    import sys, platform, traceback
    info = {
        "python": sys.version,
        "platform": platform.platform(),
        "og_version": getattr(og, "__version__", "unknown"),
        "private_key_set": bool(PRIVATE_KEY),
        "private_key_len": len(PRIVATE_KEY) if PRIVATE_KEY else 0,
        "wallet": WALLET,
        "nest_asyncio": False,
        "llm_init": None,
        "llm_error": None,
        "asyncio_test": None,
        "env_vars": [k for k in os.environ if "OG" in k or "PRIVATE" in k or "PORT" in k]
    }
    try:
        import nest_asyncio
        info["nest_asyncio"] = True
    except:
        pass
    try:
        llm = og.LLM(private_key=PRIVATE_KEY)
        info["llm_init"] = "OK"
    except Exception as e:
        info["llm_init"] = "FAIL"
        info["llm_error"] = str(e)
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.close()
        info["asyncio_test"] = "OK"
    except Exception as e:
        info["asyncio_test"] = str(e)
    try:
        import opengradient as _og
        members = [x for x in dir(_og.TEE_LLM) if not x.startswith("_")]
        info["tee_llm_members"] = members
    except Exception as e:
        info["tee_llm_members"] = str(e)
    return jsonify(info)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(debug=False, host="0.0.0.0", port=port)
