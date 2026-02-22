import streamlit as st
import opengradient as og
import os
import json
from web3 import Web3

# 1. Configuration (MUST BE FIRST)
st.set_page_config(page_title="AI Smart Contract Auditor", page_icon="🛡️", layout="wide")

# 2. Original CSS from Localhost (Extracted and Cleaned)
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;800&family=JetBrains+Mono&display=swap');

    /* Global Base */
    .stApp { background: #04060d; color: #d4dff7; font-family: 'Outfit', sans-serif; }
    [data-testid="stHeader"] { visibility: hidden; }
    
    /* Recreating the Header from index.html */
    .header-center { text-align: center; margin-bottom: 2rem; padding-top: 2rem; }
    .badge-tee { 
        display: inline-block; background: rgba(34, 197, 94, 0.1); border: 1px solid rgba(34, 197, 94, 0.2);
        color: #4ade80; padding: 4px 12px; border-radius: 20px; font-size: 0.7rem; font-weight: bold; margin-bottom: 10px;
    }
    .title-main {
        font-size: 3.5rem; font-weight: 800; line-height: 1.1;
        background: linear-gradient(135deg, #60a5fa 0%, #22d3ee 50%, #10b981 100%);
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;
        margin-bottom: 0.5rem;
    }
    .subtitle-main { color: #6b7fa8; font-size: 1rem; }

    /* Recreating the Status Bar */
    .status-container {
        max-width: 900px; margin: 0 auto 3rem; background: rgba(255, 255, 255, 0.03);
        border: 1px solid rgba(255, 255, 255, 0.1); border-radius: 12px;
        padding: 12px 25px; display: flex; justify-content: center; gap: 40px;
        font-size: 0.8rem; color: #6b7fa8; backdrop-filter: blur(10px);
    }
    .status-container b { color: #22d3ee; margin-left: 5px; font-family: 'JetBrains Mono'; }

    /* Panels (The Cards) */
    [data-testid="stVerticalBlockBorderWrapper"] {
        background: rgba(10, 14, 28, 0.9) !important;
        border: 1px solid rgba(60, 130, 255, 0.2) !important;
        border-radius: 20px !important;
        padding: 20px !important;
        box-shadow: 0 10px 40px rgba(0,0,0,0.5) !important;
    }
    
    .panel-header { font-weight: bold; font-size: 1rem; margin-bottom: 20px; display: flex; align-items: center; gap: 10px; color: #fff; }

    /* Editor and Audit Button */
    textarea { background: #080c18 !important; color: #d4dff7 !important; font-family: 'JetBrains Mono' !important; font-size: 0.85rem !important; border-radius: 12px !important; }
    
    .stButton > button[kind="primary"] {
        background: linear-gradient(135deg, #3b82f6, #22d3ee) !important;
        color: white !important; font-weight: 800 !important; border: none !important;
        border-radius: 12px !important; height: 3.5rem !important; width: 100% !important;
        box-shadow: 0 4px 20px rgba(59, 130, 246, 0.4) !important; transition: all 0.2s;
    }
    .stButton > button[kind="primary"]:hover { transform: translateY(-2px); box-shadow: 0 8px 30px rgba(59, 130, 246, 0.6) !important; }

    /* Secondary Buttons (The Pills) */
    .stButton > button[kind="secondary"] {
        border-radius: 99px !important; padding: 5px 20px !important;
        font-size: 0.72rem !important; background: rgba(255,255,255,0.05) !important;
        color: #6b7fa8 !important; border: 1px solid rgba(255,255,255,0.1) !important;
    }
    .stButton > button[kind="secondary"]:hover { color: #22d3ee !important; border-color: #22d3ee !important; }
</style>

<div class="header-center">
    <span class="badge-tee">● TEE Verification Active</span>
    <div class="title-main">Security Auditor</div>
    <div class="subtitle-main">AI-powered auditor on OpenGradient TEE</div>
</div>
""", unsafe_allow_html=True)

# 3. Backend Logic (Secret Handling)
pk = st.secrets.get("OG_PRIVATE_KEY") or os.environ.get("OG_PRIVATE_KEY")

w_addr = "0x00...00"
w_bal = "0.00"
client = None

if pk:
    try:
        client = og.Client(private_key=pk)
        w3 = Web3(Web3.HTTPProvider("https://sepolia.base.org"))
        acct = w3.eth.account.from_key(pk)
        w_addr = acct.address
        # Simplified Balance fetch
        OPG = "0x240b09731D96979f50B2C649C9CE10FcF9C7987F"
        ABI = [{"inputs":[{"name":"account","type":"address"}],"name":"balanceOf","outputs":[{"name":"","type":"uint256"}],"stateMutability":"view","type":"function"}]
        contract = w3.eth.contract(address=OPG, abi=ABI)
        w_bal = round(contract.functions.balanceOf(w_addr).call() / 1e18, 3)
    except: pass
else:
    st.error("🔑 Private Key missing in Secrets!")
    st.stop()

# 4. Status Bar
st.markdown(f"""
<div class="status-container">
    <div>Model: <b>GEMINI_2_0_FLASH</b></div>
    <div>Wallet: <b>{w_addr[:6]}...{w_addr[-4:]}</b></div>
    <div>Balance: <b>{w_bal} OPG</b></div>
    <div>Network: <b>Base Sepolia</b></div>
</div>
""", unsafe_allow_html=True)

# 5. DATA EXAMPLES
EXAMPLES = {
    "ERC-20": "// SPDX-License-Identifier: MIT\npragma solidity ^0.8.20;\nimport \"@openzeppelin/contracts/token/ERC20/ERC20.sol\";\n\ncontract MyToken is ERC20 {\n    constructor() ERC20(\"Test\", \"TST\") {\n        _mint(msg.sender, 1000 * 10**18);\n    }\n}",
    "Vulnerable": "// SPDX-License-Identifier: MIT\npragma solidity ^0.7.0;\ncontract Vulnerable {\n    mapping(address => uint) public balances;\n    function withdraw() public {\n        uint bal = balances[msg.sender];\n        require(bal > 0);\n        (bool s,) = msg.sender.call{value: bal}(\"\");\n        require(s);\n        balances[msg.sender] = 0;\n    }\n}"
}

# 6. APP LAYOUT
col_src, col_rep = st.columns(2, gap="large")

with col_src:
    with st.container(border=True):
        st.markdown('<div class="panel-header">📝 Source Code</div>', unsafe_allow_html=True)
        # Pills
        pcol1, pcol2 = st.columns(2)
        if pcol1.button("Load ERC-20 Example", key="ex_erc"):
            st.session_state.code_ed = EXAMPLES["ERC-20"]
            st.rerun()
        if pcol2.button("Load Vulnerable Code", key="ex_vuln"):
            st.session_state.code_ed = EXAMPLES["Vulnerable"]
            st.rerun()
            
        src_code = st.text_area("source", value=st.session_state.get("code_ed", ""), height=450, key="editor_box", label_visibility="collapsed")
        
        if st.button("🔍 START SECURITY AUDIT", type="primary", key="audit_btn"):
            if not client:
                st.error("SDK not initialized.")
            elif not src_code:
                st.warning("Paste code first.")
            else:
                with st.spinner("Analyzing on TEE..."):
                    try:
                        p = "Audit this code. Return raw JSON: {score: number, summary: string, findings: [{title, severity, description, recommendation}]}"
                        r = client.llm.chat(
                            model=og.TEE_LLM.GEMINI_2_0_FLASH,
                            messages=[{"role":"system","content":p}, {"role":"user","content":src_code}],
                            x402_settlement_mode=og.x402SettlementMode.SETTLE_BATCH
                        )
                        raw = r.chat_output.get("content", "")
                        if "```json" in raw: raw = raw.split("```json")[1].split("```")[0]
                        elif "```" in raw: raw = raw.split("```")[1].split("```")[0]
                        st.session_state.audit_result = json.loads(raw)
                        st.session_state.tx_hash = getattr(r, "payment_hash", None)
                        st.rerun()
                    except Exception as e: st.error(str(e))

with col_rep:
    with st.container(border=True):
        st.markdown('<div class="panel-header">📊 Audit Report</div>', unsafe_allow_html=True)
        if "audit_result" in st.session_state:
            res = st.session_state.audit_result
            score = int(res.get("score" if "score" in res else "risk_score", 0))
            clr = "#ef4444" if score > 70 else "#f97316" if score > 40 else "#10b981"
            
            st.markdown(f"""
                <div style="background:rgba(0,0,0,0.2); border-radius:15px; padding:30px; text-align:center; border:1px solid rgba(255,255,255,0.05); margin-bottom:1.5rem;">
                    <div style="font-size:0.8rem; color:#6b7fa8; text-transform:uppercase;">Security Risk Score</div>
                    <div style="font-size:4.5rem; font-weight:800; color:{clr}; line-height:1; padding:10px 0;">{score}</div>
                    <p style="font-size:0.95rem;">{res.get('summary', '')}</p>
                </div>
            """, unsafe_allow_html=True)
            
            for f in res.get("findings" if "findings" in res else "vulnerabilities", []):
                with st.expander(f"⚠️ {f.get('title')}"):
                    st.write(f.get("description" if "description" in f else "desc"))
                    st.info(f"💡 Recommendation: {f.get('recommendation', '')}")
            
            if st.session_state.get("tx_hash"):
                st.markdown(f'<div style="text-align:center; margin-top:20px;"><a href="https://sepolia.basescan.org/tx/{st.session_state.tx_hash}" target="_blank" style="color:#22d3ee; text-decoration:none; padding:10px 20px; border:1px solid rgba(34,211,238,0.2); border-radius:12px;">🔗 View On-Chain Proof</a></div>', unsafe_allow_html=True)
        else:
            st.markdown('<div style="text-align:center; padding-top:150px; opacity:0.2;">🛡️ Paste code and click Start Audit</div>', unsafe_allow_html=True)
