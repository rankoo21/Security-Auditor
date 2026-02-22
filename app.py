import os, json, hashlib, time
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
        p = "Audit this Solidity contract. Return ONLY valid JSON with keys: {summary, risk_score, vulnerabilities: [{title, severity, description, recommendation}]}. No other text."
        result = client.llm.chat(
            model=og.TEE_LLM.GEMINI_2_0_FLASH,
            messages=[{"role": "system", "content": p}, {"role": "user", "content": code}],
            max_tokens=2048,
            temperature=0.1,
            x402_settlement_mode=og.x402SettlementMode.SETTLE_BATCH
        )
        
        raw_output = result.chat_output.get("content", "").strip()
        
        # Robust JSON extraction
        clean_json = raw_output
        if "```json" in clean_json:
            clean_json = clean_json.split("```json")[1].split("```")[0]
        elif "```" in clean_json:
            clean_json = clean_json.split("```")[1].split("```")[0]
            
        clean_json = clean_json.strip()
        
        try:
            parsed = json.loads(clean_json)
        except json.JSONDecodeError:
            # Try to fix truncated JSON if possible or return raw with error
            import re
            # Simple attempt to find the first { and last }
            match = re.search(r'(\{.*\})', clean_json, re.DOTALL)
            if match:
                try:
                    parsed = json.loads(match.group(1))
                except:
                    raise Exception("AI returned malformed JSON. Please try again.")
            else:
                raise Exception("Could not find valid JSON in AI response.")

        parsed["payment_hash"] = getattr(result, "payment_hash", None)
        return jsonify({"success": True, "audit": parsed})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

# Vercel needs the app object
if __name__ == "__main__":
    app.run(debug=True)
