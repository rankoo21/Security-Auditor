import os, json, hashlib, time, re
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import opengradient as og
from web3 import Web3

app = Flask(__name__, static_folder="static")
CORS(app)

# Environment Variables
PRIVATE_KEY = os.environ.get("OG_PRIVATE_KEY")

# Simple check for Key
def get_client():
    if not PRIVATE_KEY:
        return None
    try:
        # Format key correctly
        pk = PRIVATE_KEY.strip()
        if not pk.startswith("0x"): pk = "0x" + pk
        return og.Client(private_key=pk)
    except:
        return None

def get_opg_balance(wa):
    try:
        w3 = Web3(Web3.HTTPProvider("https://sepolia.base.org"))
        OPG_ADDR = "0x240b09731D96979f50B2C649C9CE10FcF9C7987F"
        ABI = [{"inputs":[{"name":"account","type":"address"}],"name":"balanceOf","outputs":[{"name":"","type":"uint256"}],"stateMutability":"view","type":"function"}]
        contract = w3.eth.contract(address=OPG_ADDR, abi=ABI)
        bal = contract.functions.balanceOf(wa).call()
        return round(bal / 1e18, 4)
    except:
        return 0.0

@app.route("/")
def index():
    return send_from_directory("static", "index.html")

@app.route("/api/status")
def status():
    wa = "0x00...00"
    bal = 0.0
    if PRIVATE_KEY:
        try:
            w3 = Web3(Web3.HTTPProvider("https://sepolia.base.org"))
            acct = w3.eth.account.from_key(PRIVATE_KEY)
            wa = acct.address
            bal = get_opg_balance(wa)
        except: pass
        
    return jsonify({
        "wallet": wa,
        "balance": bal,
        "model": "GEMINI_2_0_FLASH",
        "status": "ready" if PRIVATE_KEY else "missing_key"
    })

def repair_json(s):
    """Simple helper to close truncated JSON strings/objects."""
    s = s.strip()
    # Count open/close braces
    open_b = s.count('{')
    close_b = s.count('}')
    if open_b > close_b:
        s += '}' * (open_b - close_b)
    
    # Check if inside an array
    open_a = s.count('[')
    close_a = s.count(']')
    if open_a > close_a:
        # This is a bit complex, but usually it's inside a list of vulnerabilities
        # We try to close the current object if needed, then close the array
        if s.endswith('}') or s.strip().endswith('}'):
            s += ']'
        else:
            s += '}]' # Close object and array
            
    # Final check: if still missing the root closing brace
    if s.count('{') > s.count('}'):
        s += '}'
        
    return s

@app.route("/api/audit", methods=["POST"])
def audit():
    data = request.get_json(force=True) or {}
    code = data.get("code", "").strip()
    
    if not code:
        return jsonify({"success": False, "error": "No code provided"}), 400
    
    client = get_client()
    if not client:
        return jsonify({"success": False, "error": "SDK not initialized. Set OG_PRIVATE_KEY."}), 500

    try:
        # Prompting for a more compact response to avoid truncation
        p = "Audit this contract. Return ONLY a concise JSON (max 5 findings) with keys: {summary, risk_score, vulnerabilities:[{title, severity, description, recommendation}]}"
        
        result = client.llm.chat(
            model=og.TEE_LLM.GEMINI_2_0_FLASH,
            messages=[{"role": "system", "content": p}, {"role": "user", "content": code}],
            max_tokens=1500, # Increased but kept safe
            temperature=0.1,
            x402_settlement_mode=og.x402SettlementMode.SETTLE_BATCH
        )
        
        raw_output = result.chat_output.get("content", "").strip()
        
        # Extract JSON from potential markdown
        clean_json = raw_output
        if "```json" in clean_json:
            clean_json = clean_json.split("```json")[1].split("```")[0]
        elif "```" in clean_json:
            clean_json = clean_json.split("```")[1].split("```")[0]
            
        clean_json = clean_json.strip()
        
        # Try PARSING
        try:
            parsed = json.loads(clean_json)
        except json.JSONDecodeError:
            # TRY REPAIRING
            try:
                repaired = repair_json(clean_json)
                parsed = json.loads(repaired)
            except:
                # If still fails, try regex extraction
                match = re.search(r'(\{.*\})', clean_json, re.DOTALL)
                if match:
                    try:
                        parsed = json.loads(repair_json(match.group(1)))
                    except:
                        raise Exception("AI response truncated too early. Please try a smaller code snippet.")
                else:
                    raise Exception("Invalid response format from AI.")

        parsed["payment_hash"] = getattr(result, "payment_hash", None)
        return jsonify({"success": True, "audit": parsed})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

# Vercel needs the app object
if __name__ == "__main__":
    app.run(debug=True)
