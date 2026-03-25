"""
Auditor - Powered by OpenGradient SDK
Uses direct IP (3.15.214.21) to bypass DNS issue with llm.opengradient.ai
"""
import os, json, threading, time, hashlib, re, ssl

# ── SSL Fix: must happen BEFORE any imports that touch httpx/ssl ─────
# Disable all SSL verification globally
os.environ["PYTHONHTTPSVERIFY"] = "0"
os.environ["CURL_CA_BUNDLE"] = ""
os.environ["REQUESTS_CA_BUNDLE"] = ""

ssl._create_default_https_context = ssl._create_unverified_context

try:
    import urllib3
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
except Exception:
    pass

try:
    import httpx
    import httpx._config as _hcfg
    # Force SSL=False in all new httpx clients by patching the default
    _orig_async_init = httpx.AsyncClient.__init__
    def _async_init_nossl(self, *args, **kwargs):
        kwargs.setdefault("verify", False)
        _orig_async_init(self, *args, **kwargs)
    httpx.AsyncClient.__init__ = _async_init_nossl

    _orig_sync_init = httpx.Client.__init__
    def _sync_init_nossl(self, *args, **kwargs):
        kwargs.setdefault("verify", False)
        _orig_sync_init(self, *args, **kwargs)
    httpx.Client.__init__ = _sync_init_nossl
    print("[SSL] httpx patched: verify=False globally")
except Exception as _e:
    print(f"[SSL] httpx patch skipped: {_e}")

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

# Direct IP workaround: llm.opengradient.ai DNS is broken,
# using IP from OpenGradient community (Trungkts)
OG_LLM_SERVER = "https://3.15.214.21"

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

# Models — keys must match the 'value' attributes in the frontend dropdown
def _m(name, fallback=None):
    """Safely get a TEE_LLM enum member by name."""
    val = getattr(og.TEE_LLM, name, None)
    if val is not None:
        return val
    if fallback:
        return getattr(og.TEE_LLM, fallback, og.TEE_LLM.GEMINI_2_0_FLASH)
    return og.TEE_LLM.GEMINI_2_0_FLASH

MODELS = {
    # Legacy keys (kept for backward compat)
    "GEMINI_2_0_FLASH":      _m("GEMINI_2_0_FLASH"),
    "GEMINI_1_5_FLASH":      _m("GEMINI_1_5_FLASH",      "GEMINI_2_0_FLASH"),
    "GPT_4O":                _m("GPT_4O",                "GPT_4_1_2025_04_14"),
    "GPT_4_1_2025_04_14":    _m("GPT_4_1_2025_04_14"),
    "CLAUDE_3_7_SONNET":     _m("CLAUDE_3_7_SONNET",     "GEMINI_2_0_FLASH"),
    # Front-end dropdown values
    "GEMINI_2_5_FLASH":      _m("GEMINI_2_5_FLASH",      "GEMINI_2_0_FLASH"),
    "GEMINI_2_5_PRO":        _m("GEMINI_2_5_PRO",        "GEMINI_2_5_FLASH"),
    "GEMINI_3_FLASH":        _m("GEMINI_3_FLASH",        "GEMINI_2_5_FLASH"),
    "GPT_5_MINI":            _m("GPT_5_MINI",            "GPT_4_1_2025_04_14"),
    "GPT_5":                 _m("GPT_5",                 "GPT_4_1_2025_04_14"),
    "O4_MINI":               _m("O4_MINI",               "GPT_4_1_2025_04_14"),
    "CLAUDE_HAIKU_4_5":      _m("CLAUDE_HAIKU_4_5",      "GEMINI_2_0_FLASH"),
    "CLAUDE_SONNET_4_5":     _m("CLAUDE_SONNET_4_5",     "GEMINI_2_0_FLASH"),
    "GROK_4_FAST":           _m("GROK_4_FAST",           "GEMINI_2_0_FLASH"),
}

ACTIVE_MODEL = og.TEE_LLM.GEMINI_2_0_FLASH
ACTIVE_MODEL_NAME = "GEMINI_2_0_FLASH"

# ── Patched Client: skip SSL verification for direct IP ─────────────
def _deep_patch_ssl(client):
    """Deep-patch the og.Client's internal httpx transports to skip SSL verify."""
    try:
        import asyncio

        async def _patch():
            llm = client.llm
            # Try patching the underlying x402 httpx clients via their transport
            for attr in ["_request_client", "_stream_client"]:
                c = getattr(llm, attr, None)
                if c and hasattr(c, "_transport"):
                    try:
                        c._transport._pool._ssl_context.check_hostname = False
                        c._transport._pool._ssl_context.verify_mode = ssl.CERT_NONE
                        print(f"[SSL] Patched {attr}._transport ssl_context")
                    except Exception as _ex:
                        print(f"[SSL] Transport patch failed for {attr}: {_ex}")

            # Also try rebuilding via x402HttpxClient
            try:
                from x402v2.http.clients import x402HttpxClient as _x402
                if llm._request_client_ctx:
                    await llm._request_client_ctx.__aexit__(None, None, None)
                if llm._stream_client_ctx:
                    await llm._stream_client_ctx.__aexit__(None, None, None)
                llm._request_client_ctx = _x402(llm._x402_client, verify=False)
                llm._request_client = await llm._request_client_ctx.__aenter__()
                llm._stream_client_ctx = _x402(llm._x402_client, verify=False)
                llm._stream_client = await llm._stream_client_ctx.__aenter__()
                print("[SSL] Rebuilt x402HttpxClient with verify=False")
            except Exception as _ex2:
                print(f"[SSL] x402 rebuild failed: {_ex2}")

        client.llm._run_coroutine(_patch())
    except Exception as e:
        print(f"[SSL] deep_patch_ssl error: {e}")

def make_client():
    """Create og.Client. First tries direct IP with SSL bypass, falls back to default."""
    if not PRIVATE_KEY:
        return None

    # Attempt 1: Direct IP + SSL bypass
    try:
        client = og.Client(
            private_key=PRIVATE_KEY,
            og_llm_server_url=OG_LLM_SERVER,
            og_llm_streaming_server_url=OG_LLM_SERVER
        )
        _deep_patch_ssl(client)
        return client
    except Exception as e:
        print(f"[Client] Direct IP init error: {e}")

    # Attempt 2: Default URL (DNS might work now)
    try:
        print("[Client] Trying default og.Client() without IP override...")
        client = og.Client(private_key=PRIVATE_KEY)
        return client
    except Exception as e:
        print(f"[Client] Default init error: {e}")
        return None

# ── System prompt ───────────────────────────────────────────────────
AUDIT_SYSTEM_PROMPT = """You are a professional senior Solidity smart contract security auditor.
You MUST respond with valid JSON ONLY. No markdown, no code fences, no extra text.

ANALYSIS RULES:
1. VERSION AWARENESS: Detect pragma version. If >=0.8.0, do NOT flag overflow/underflow. SafeMath is unnecessary.
2. EXPLOITABLE ONLY: Report only real exploitable vulnerabilities with technical justification (exploit scenario, impact, likelihood).
3. REENTRANCY: Only flag if state updates occur AFTER external call. If CEI pattern is followed, state "No reentrancy detected."
4. ACCESS CONTROL: Only flag missing access control on sensitive state-changing functions.
5. FALSE POSITIVE AVOIDANCE: Do NOT hallucinate issues. Every finding must have a realistic attack path.
6. EVENTS: Missing events are LOW/informational severity only.
7. GAS: Gas optimizations are informational only, never vulnerabilities.

SEVERITY LEVELS: critical, high, medium, low, info

JSON Structure:
{
  "summary": "1-2 sentences professional assessment",
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
    {"title": "Practice", "status": "pass|fail", "note": "Note"}
  ]
}

CRITICAL OUTPUT RULES:
- Max 5 vulnerabilities, 3 gas optimizations, 4 best practices.
- Keep descriptions concise (1-2 sentences max).
- Keep total response under 900 tokens.
- Clearly state if no critical vulnerabilities exist.
- All text in English."""

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

# ── Flask routes ────────────────────────────────────────────────────

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
RETRY_DELAY = 2

@app.route("/api/audit", methods=["POST","OPTIONS"])
def audit():
    if request.method == "OPTIONS":
        return jsonify({}), 200

    data = request.get_json(force=True) or {}
    code = data.get("code", "").strip()
    req_model = data.get("model", "GEMINI_2_0_FLASH")

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
        client = None
        try:
            client = make_client()
            if not client:
                return jsonify({"success": False, "error": "SDK not initialized. Check OG_PRIVATE_KEY."}), 500

            print(f"[Audit] Attempt {attempt}/{MAX_RETRIES} with {target_model_name} via {OG_LLM_SERVER}...")

            with llm_lock:
                result = client.llm.chat(
                    model=target_model,
                    messages=messages,
                    max_tokens=2000,
                    temperature=0.1,
                    x402_settlement_mode=og.x402SettlementMode.SETTLE_BATCH
                )

            raw = (result.chat_output or {}).get("content", "") or ""
            phash = getattr(result, "payment_hash", None)
            parsed = parse_llm_json(raw)

            if parsed:
                print(f"[Audit] Attempt {attempt} SUCCESS!")
                break
            else:
                print(f"[Audit] Attempt {attempt}: got response but JSON parse failed")
                last_error = "LLM response could not be parsed as JSON"

        except Exception as e:
            last_error = str(e)
            print(f"[Audit] Attempt {attempt} error: {last_error}")

        finally:
            if client:
                try:
                    client.close()
                except:
                    pass

        if attempt < MAX_RETRIES:
            delay = RETRY_DELAY * attempt
            print(f"[Audit] Waiting {delay}s before retry...")
            time.sleep(delay)

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

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(debug=False, host="0.0.0.0", port=port)
