import streamlit as st
import opengradient as og
import os
import json
from web3 import Web3

# 1. Page Config
st.set_page_config(page_title="Security Auditor", page_icon="🛡️", layout="wide")

# 2. Initialization with Caching (Critical for SDK Stability)
@st.cache_resource
def get_og_client(pk):
    if not pk: return None
    try:
        return og.Client(private_key=pk)
    except:
        return None

# 3. CSS Injection (Pure string to avoid TokenError)
# We use standard strings (not f-strings) for the CSS block
CSS_BASE = """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;800&family=JetBrains+Mono&display=swap');

    .stApp { background: #04060d; color: #d4dff7; font-family: 'Outfit', sans-serif; }
    [data-testid="stHeader"] { visibility: hidden; }
    
    .main-title {
        text-align: center; font-size: 3.5rem; font-weight: 800; margin-top: 1rem;
        background: linear-gradient(135deg, #60a5fa 0%, #22d3ee 50%, #10b981 100%);
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;
        padding: 20px 0;
    }
    
    .status-bar {
        display: flex; justify-content: center; gap: 30px; 
        background: rgba(255,255,255,0.03); border: 1px solid rgba(255,255,255,0.1);
        border-radius: 12px; padding: 12px 25px; margin: 0 auto 40px; max-width: 900px;
        font-size: 0.8rem; color: #6b7fa8; backdrop-filter: blur(10px);
    }
    .status-bar b { color: #22d3ee; margin-left: 5px; font-family: 'JetBrains Mono'; }

    /* Panels UI */
    [data-testid="stVerticalBlockBorderWrapper"] {
        background: rgba(10, 14, 28, 0.95) !important;
        border: 1px solid rgba(60, 130, 255, 0.2) !important;
        border-radius: 20px !important;
        padding: 25px !important;
        box-shadow: 0 10px 40px rgba(0,0,0,0.5) !important;
    }
    
    .panel-title { font-weight: 700; font-size: 1rem; margin-bottom: 20px; color: #fff; display: flex; align-items: center; gap: 10px; }

    /* Inputs & Buttons */
    div[data-baseweb="textarea"] { background: #080c18 !important; border: 1px solid rgba(255,255,255,0.1) !important; border-radius: 12px !important; }
    textarea { color: #d4dff7 !important; font-family: 'JetBrains Mono' !important; font-size: 0.85rem !important; }
    
    .stButton > button[kind="primary"] {
        background: linear-gradient(135deg, #3b82f6, #22d3ee) !important;
        color: white !important; font-weight: 800 !important; border: none !important;
        height: 3.5rem !important; width: 100% !important; border-radius: 12px !important;
        box-shadow: 0 4px 20px rgba(59, 130, 246, 0.4) !important;
    }
    
    .stButton > button[kind="secondary"] {
        border-radius: 99px !important; background: rgba(255,255,255,0.05) !important;
        color: #6b7fa8 !important; border: 1px solid rgba(255,255,255,0.1) !important;
        font-size: 0.72rem !important; padding: 5px 20px !important;
    }
</style>
"""
st.markdown(CSS_BASE, unsafe_allow_html=True)

# 4. Data Logic
pk = st.secrets.get("OG_PRIVATE_KEY") or os.environ.get("OG_PRIVATE_KEY")
client = get_og_client(pk)

wallet_addr = "0x000...000"
balance = "0.00"

if pk:
    try:
        w3 = Web3(Web3.HTTPProvider("https://sepolia.base.org"))
        acct = w3.eth.account.from_key(pk)
        wallet_addr = acct.address
        # Fetch Balance
        OPG_TOKEN = "0x240b09731D96979f50B2C649C9CE10FcF9C7987F"
        ABI = [{"inputs":[{"name":"account","type":"address"}],"name":"balanceOf","outputs":[{"name":"","type":"uint256"}],"stateMutability":"view","type":"function"}]
        contract = w3.eth.contract(address=OPG_TOKEN, abi=ABI)
        balance = round(contract.functions.balanceOf(wallet_addr).call() / 1e18, 3)
    except: pass
else:
    st.error("🔑 Private Key missing in Secrets!")
    st.stop()

# 5. Header & Status Bar
st.markdown('<div class="main-title">Security Auditor</div>', unsafe_allow_html=True)
st.markdown(f"""
<div class="status-bar">
    <div>Model: <b>GEMINI_2_0_FLASH</b></div>
    <div>Wallet: <b>{wallet_addr[:8]}...{wallet_addr[-6:]}</b></div>
    <div>Balance: <b>{balance} OPG</b></div>
    <div>Network: <b>Base Sepolia</b></div>
</div>
""", unsafe_allow_html=True)

# 6. Examples
EXAMPLES = {
    "ERC-20 Example": "// SPDX-License-Identifier: MIT\npragma solidity ^0.8.20;\nimport \"@openzeppelin/contracts/token/ERC20/ERC20.sol\";\n\ncontract MyToken is ERC20 {\n    constructor() ERC20(\"RankoToken\", \"RNK\") {\n        _mint(msg.sender, 1000000 * 10**18);\n    }\n}",
    "Vulnerable Code": "// SPDX-License-Identifier: MIT\npragma solidity ^0.7.0;\n\ncontract Vulnerable {\n    mapping(address => uint256) public balances;\n    function withdraw(uint256 amount) public {\n        require(balances[msg.sender] >= amount);\n        (bool ok, ) = msg.sender.call{value: amount}(\"\");\n        require(ok);\n        balances[msg.sender] -= amount;\n    }\n}",
    "Reentrancy": "// SPDX-License-Identifier: MIT\npragma solidity ^0.8.0;\n\ncontract Bank {\n    mapping(address => uint) public balances;\n    function withdraw() public {\n        uint bal = balances[msg.sender];\n        require(bal > 0);\n        (bool sent,) = msg.sender.call{value: bal}(\"\");\n        require(sent);\n        balances[msg.sender] = 0;\n    }\n}"
}

# 7. Main Grid
col1, col2 = st.columns(2, gap="large")

with col1:
    with st.container(border=True):
        st.markdown('<div class="panel-title">📝 Source Code</div>', unsafe_allow_html=True)
        
        # Example Buttons
        ex_cols = st.columns(3)
        if ex_cols[0].button("ERC-20 Example", key="b_erc"):
            st.session_state.editor_code = EXAMPLES["ERC-20 Example"]
        if ex_cols[1].button("Vulnerable Code", key="b_vuln"):
            st.session_state.editor_code = EXAMPLES["Vulnerable Code"]
        if ex_cols[2].button("Reentrancy", key="b_reen"):
            st.session_state.editor_code = EXAMPLES["Reentrancy"]
            
        current_code = st.text_area("source", value=st.session_state.get("editor_code", ""), height=450, key="audit_editor", label_visibility="collapsed")
        
        if st.button("🔍 START SECURITY AUDIT", type="primary", key="main_audit_btn"):
            if not client:
                st.error("❌ SDK Client not initialized. Check your Private Key.")
            elif not current_code:
                st.warning("⚠️ Please paste code first.")
            else:
                with st.spinner("TEE Analysis in progress..."):
                    try:
                        prompt = "Audit this contract. Return JSON {score, summary, findings:[{title, severity, description, recommendation}]}"
                        resp = client.llm.chat(
                            model=og.TEE_LLM.GEMINI_2_0_FLASH,
                            messages=[{"role":"system","content":prompt}, {"role":"user","content":current_code}],
                            x402_settlement_mode=og.x402SettlementMode.SETTLE_BATCH
                        )
                        raw = resp.chat_output.get("content", "")
                        if "```json" in raw: raw = raw.split("```json")[1].split("```")[0]
                        st.session_state.audit_report = json.loads(raw)
                        st.session_state.audit_tx = getattr(resp, "payment_hash", None)
                        st.rerun()
                    except Exception as e:
                        st.error(f"Audit Error: {e}")

with col2:
    with st.container(border=True):
        st.markdown('<div class="panel-title">📊 Analysis Report</div>', unsafe_allow_html=True)
        if "audit_report" in st.session_state:
            res = st.session_state.audit_report
            score = int(res.get("score" if "score" in res else "risk_score", 0))
            color = "#ef4444" if score > 70 else "#f97316" if score > 40 else "#10b981"
            
            st.markdown(f"""
                <div style="background:rgba(0,0,0,0.2); border-radius:15px; padding:30px; text-align:center; border:1px solid rgba(255,255,255,0.05); margin-bottom:1.5rem;">
                    <div style="font-size:0.8rem; color:#6b7fa8; text-transform:uppercase; letter-spacing:1px;">Risk Score</div>
                    <div style="font-size:4.5rem; font-weight:800; color:{color}; line-height:1; margin:10px 0;">{score}</div>
                    <p style="font-size:0.95rem; opacity:0.9;">{res.get('summary','')}</p>
                </div>
            """, unsafe_allow_html=True)
            
            for f in res.get("findings" if "findings" in res else "vulnerabilities", []):
                with st.expander(f"⚠️ {f.get('title')}"):
                    st.write(f.get("description" if "description" in f else "desc"))
                    st.info(f"💡 Recommendation: {f.get('recommendation', '')}")
            
            if st.session_state.get("audit_tx"):
                st.markdown(f'<div style="text-align:center; margin-top:20px;"><a href="https://sepolia.basescan.org/tx/{st.session_state.audit_tx}" target="_blank" style="color:#22d3ee; text-decoration:none; padding:10px 20px; border:1px solid rgba(34,211,238,0.2); border-radius:12px; background:rgba(34,211,238,0.05);">🔗 View On-Chain Proof</a></div>', unsafe_allow_html=True)
        else:
            st.markdown('<div style="text-align:center; padding-top:150px; opacity:0.2; font-size:1.1rem;">🛡️ Paste source code to generate persistent report</div>', unsafe_allow_html=True)
