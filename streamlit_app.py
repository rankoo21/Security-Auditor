import streamlit as st
import opengradient as og
import os
import json
from web3 import Web3

# 1. Page Config
st.set_page_config(page_title="Security Auditor", page_icon="🛡️", layout="wide")

# 2. CSS Injection (Standard way to avoid DOM issues)
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;800&family=JetBrains+Mono&display=swap');

    .stApp { background: #04060d; color: #d4dff7; font-family: 'Outfit', sans-serif; }
    [data-testid="stHeader"] { visibility: hidden; }
    
    /* Global Title */
    .title-box { text-align: center; padding: 1.5rem 0; }
    .title-text { 
        font-size: 3.2rem; font-weight: 800; 
        background: linear-gradient(135deg, #60a5fa 0%, #22d3ee 50%, #10b981 100%);
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;
        filter: drop-shadow(0 0 10px rgba(59, 130, 246, 0.2));
    }
    
    /* Info Bar */
    .info-bar {
        display: flex; justify-content: center; gap: 25px; 
        background: rgba(255,255,255,0.03); border: 1px solid rgba(255,255,255,0.08);
        border-radius: 10px; padding: 10px; margin-bottom: 2rem;
        font-size: 0.75rem; color: #6b7fa8;
    }
    .info-bar b { color: #22d3ee; margin-left: 4px; font-family: 'JetBrains Mono'; }

    /* Custom Containers */
    [data-testid="stVerticalBlockBorderWrapper"] {
        background: rgba(10, 14, 28, 0.9) !important;
        border: 1px solid rgba(60, 130, 255, 0.2) !important;
        border-radius: 20px !important;
        padding: 10px !important;
    }
    
    /* Inputs */
    div[data-baseweb="textarea"] { background: #080c18 !important; border-radius: 12px !important; }
    textarea { color: #d4dff7 !important; font-family: 'JetBrains Mono' !important; font-size: 0.82rem !important; }

    /* Buttons */
    button[kind="secondary"] {
        border-radius: 99px !important; padding: 4px 15px !important;
        font-size: 0.7rem !important; background: rgba(255,255,255,0.05) !important;
    }
    
    .stButton > button[kind="primary"] {
        background: linear-gradient(135deg, #3b82f6, #22d3ee) !important;
        width: 100% !important; border: none !important; height: 3.5rem !important;
        font-weight: 800 !important; font-size: 1rem !important;
        box-shadow: 0 4px 15px rgba(59, 130, 246, 0.3) !important;
    }
</style>
""", unsafe_allow_html=True)

# 3. Initialization
pk = st.secrets.get("OG_PRIVATE_KEY") or os.environ.get("OG_PRIVATE_KEY")

client = None
if pk:
    try: client = og.Client(private_key=pk)
    except: pass

wallet_addr = "0x00...00"
balance = "0.00"
if pk:
    try:
        w3 = Web3(Web3.HTTPProvider("https://sepolia.base.org"))
        acct = w3.eth.account.from_key(pk)
        wallet_addr = acct.address
        OPG_TOKEN = "0x240b09731D96979f50B2C649C9CE10FcF9C7987F"
        ABI = [{"inputs":[{"name":"account","type":"address"}],"name":"balanceOf","outputs":[{"name":"","type":"uint256"}],"stateMutability":"view","type":"function"}]
        tkn = w3.eth.contract(address=OPG_TOKEN, abi=ABI)
        balance = round(tkn.functions.balanceOf(wallet_addr).call() / 1e18, 3)
    except: pass

# 4. Header UI
st.markdown('<div class="title-box"><div class="title-text">Security Auditor</div><div style="color:#6b7fa8;">AI-Powered TEE Security Analysis</div></div>', unsafe_allow_html=True)
st.markdown(f'''
<div class="info-bar">
    <div>Model: <b>GEMINI_2_0_FLASH</b></div>
    <div>Wallet: <b>{wallet_addr[:6]}...{wallet_addr[-4:]}</b></div>
    <div>Balance: <b>{balance} OPG</b></div>
</div>
''', unsafe_allow_html=True)

# 5. Data
EXAMPLES = {
    "ERC-20": "// SPDX-License-Identifier: MIT\npragma solidity ^0.8.20;\nimport \"@openzeppelin/contracts/token/ERC20/ERC20.sol\";\n\ncontract MyToken is ERC20 {\n    constructor() ERC20(\"Test\", \"TST\") {\n        _mint(msg.sender, 1000 * 10**18);\n    }\n}",
    "Reentrancy": "// SPDX-License-Identifier: MIT\npragma solidity ^0.8.0;\ncontract Vulnerable {\n    mapping(address => uint) public balances;\n    function withdraw() public {\n        uint bal = balances[msg.sender];\n        require(bal > 0);\n        (bool s,) = msg.sender.call{value: bal}(\"\");\n        require(s);\n        balances[msg.sender] = 0;\n    }\n}"
}

# 6. Main App
col1, col2 = st.columns(2, gap="large")

with col1:
    with st.container(border=True):
        st.subheader("📝 Source Code")
        c1, c2 = st.columns(2)
        if c1.button("Load ERC-20", key="b1"):
            st.session_state.editor = EXAMPLES["ERC-20"]
            st.rerun()
        if c2.button("Load Reentrancy", key="b2"):
            st.session_state.editor = EXAMPLES["Reentrancy"]
            st.rerun()
            
        code = st.text_area("Source Code", height=400, key="editor", label_visibility="collapsed")
        
        if st.button("🔍 START SCAN", type="primary", key="scan"):
            if not client: st.error("SDK Client error")
            elif not code: st.warning("Paste code first")
            else:
                with st.spinner("Analyzing on TEE..."):
                    try:
                        p = "Analyze for bugs. Return JSON {risk_score, summary, vulnerabilities:[{title, description, severity}]}"
                        r = client.llm.chat(
                            model=og.TEE_LLM.GEMINI_2_0_FLASH,
                            messages=[{"role":"system","content":p}, {"role":"user","content":code}],
                            x402_settlement_mode=og.x402SettlementMode.SETTLE_BATCH
                        )
                        raw = r.chat_output.get("content", "")
                        if "```json" in raw: raw = raw.split("```json")[1].split("```")[0]
                        elif "```" in raw: raw = raw.split("```")[1].split("```")[0]
                        st.session_state.report = json.loads(raw)
                        st.session_state.tx_id = getattr(r, "payment_hash", None)
                        st.rerun()
                    except Exception as e: st.error(f"Error: {e}")

with col2:
    with st.container(border=True):
        st.subheader("📊 Audit Report")
        if "report" in st.session_state:
            rep = st.session_state.report
            score = int(rep.get("risk_score", 0))
            clr = "#ef4444" if score > 70 else "#f97316" if score > 40 else "#10b981"
            st.markdown(f"""
                <div style="text-align:center; padding:20px; background:rgba(0,0,0,0.2); border-radius:12px;">
                    <div style="font-size:0.8rem; color:#6b7fa8;">RISK SCORE</div>
                    <div style="font-size:4rem; font-weight:800; color:{clr};">{score}</div>
                    <p>{rep.get('summary','')}</p>
                </div>
            """, unsafe_allow_html=True)
            
            for v in rep.get("vulnerabilities", []):
                with st.expander(f"⚠️ {v.get('title')}"):
                    st.write(v.get("description"))
            
            if st.session_state.get("tx_id"):
                st.markdown(f'<div style="text-align:center; margin-top:20px;"><a href="https://sepolia.basescan.org/tx/{st.session_state.tx_id}" target="_blank" style="color:#22d3ee; text-decoration:none;">🔗 View On-Chain Proof</a></div>', unsafe_allow_html=True)
        else:
            st.markdown('<div style="text-align:center; padding-top:100px; opacity:0.2;">🛡️ Paste code to start</div>', unsafe_allow_html=True)
