import streamlit as st
import opengradient as og
import os
import json
from web3 import Web3

# 1. Config (First line)
st.set_page_config(page_title="AI Security Auditor", page_icon="🛡️", layout="wide")

# 2. CSS Reset & Restoration (Exact Localhost Variables)
st.markdown(r"""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;700;800&family=JetBrains+Mono&display=swap');

    :root {
        --void: #04060d; --deep: #080c18; --text: #d4dff7; --muted: #6b7fa8;
        --cyan: #22d3ee; --blue1: #3b82f6; --green: #10b981;
    }

    .stApp { background: var(--void); color: var(--text); font-family: 'Outfit', sans-serif; }
    [data-testid="stHeader"] { visibility: hidden; }
    
    /* Header Restoration */
    .title-box { text-align: center; padding: 40px 0 10px; }
    .title-text {
        font-size: 3.5rem; font-weight: 800; line-height: 1.1;
        background: linear-gradient(135deg, #60a5fa 0%, #22d3ee 50%, #10b981 100%);
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;
        filter: drop-shadow(0 0 15px rgba(59,130,246,0.3));
    }
    
    /* Status Bar */
    .status-bar-og {
        display: flex; justify-content: center; gap: 30px; 
        background: rgba(40, 120, 255, 0.05); border: 1px solid rgba(60, 130, 255, 0.2);
        border-radius: 12px; padding: 12px 25px; margin: 10px auto 35px; max-width: 950px;
        font-size: 0.8rem; color: var(--muted); backdrop-filter: blur(10px);
    }
    .status-bar-og b { color: var(--cyan); font-family: 'JetBrains Mono'; }

    /* Panels */
    [data-testid="stVerticalBlockBorderWrapper"] {
        background: rgba(10, 14, 28, 0.95) !important;
        border: 1px solid rgba(60, 130, 255, 0.25) !important;
        border-radius: 20px !important; padding: 25px !important;
    }
    
    .panel-hdr { font-weight: 800; font-size: 1.1rem; color: #fff; margin-bottom: 20px; display: flex; align-items: center; gap: 10px; }

    /* Editor */
    div[data-baseweb="textarea"] { background: var(--deep) !important; border: 1px solid rgba(255,255,255,0.1) !important; border-radius: 12px !important; }
    textarea { color: var(--text) !important; font-family: 'JetBrains Mono' !important; font-size: 0.88rem !important; }
    
    /* Buttons */
    .stButton > button { border-radius: 12px !important; font-weight: 700 !important; transition: 0.2s; }
    button[kind="primary"] {
        background: linear-gradient(135deg, var(--blue1), var(--cyan)) !important;
        color: white !important; height: 3.5rem !important; width: 100% !important; border: none !important;
    }
    
    /* Pills */
    [key^="pill"] button {
        background: rgba(255,255,255,0.04) !important; color: var(--muted) !important; 
        border: 1px solid rgba(255,255,255,0.1) !important; border-radius: 99px !important;
        font-size: 0.72rem !important; padding: 4px 18px !important;
    }
</style>
""", unsafe_allow_html=True)

# 3. Robust SDK Initialization
pk = (st.secrets.get("OG_PRIVATE_KEY") or os.environ.get("OG_PRIVATE_KEY") or "").strip()
if pk and not pk.startswith("0x") and len(pk) == 64: pk = "0x" + pk

client = None
wallet_addr = "0x000...000"
balance = "0.00"

if pk:
    try:
        # Direct Load (No Cache)
        client = og.Client(private_key=pk)
        w3 = Web3(Web3.HTTPProvider("https://sepolia.base.org"))
        acct = w3.eth.account.from_key(pk)
        wallet_addr = acct.address
        # Real Balance
        OPG = "0x240b09731D96979f50B2C649C9CE10FcF9C7987F"
        ABI = [{"inputs":[{"name":"account","type":"address"}],"name":"balanceOf","outputs":[{"name":"","type":"uint256"}],"stateMutability":"view","type":"function"}]
        c = w3.eth.contract(address=OPG, abi=ABI)
        balance = "{:.3f}".format(c.functions.balanceOf(wallet_addr).call() / 1e18)
    except Exception as e:
        st.error(f"⚠️ SDK Initialization Failed: {e}")

# 4. Header UI
st.markdown(f"""
<div class="title-box">
    <div class="title-text">Security Auditor</div>
    <div style="color:var(--muted); font-size:1.1rem; margin-top:5px;">AI-Powered Security Analyst on OpenGradient</div>
</div>
<div class="status-bar-og">
    <div>Model: <b>GEMINI_2_0_FLASH</b></div>
    <div>Wallet: <b>{wallet_addr[:8]}...{wallet_addr[-6:]}</b></div>
    <div>Balance: <b>{balance} OPG</b></div>
    <div>Network: <b>Base Sepolia</b></div>
</div>
""", unsafe_allow_html=True)

# 5. Examples
EXAMPLES = {
    "ERC-20": "// SPDX-License-Identifier: MIT\npragma solidity ^0.8.20;\nimport \"@openzeppelin/contracts/token/ERC20/ERC20.sol\";\ncontract MyToken is ERC20 { constructor() ERC20(\"Test\", \"TST\") { _mint(msg.sender, 1000 * 10**18); } }",
    "Vulnerable": "// SPDX-License-Identifier: MIT\npragma solidity ^0.7.0;\ncontract Bank { function pull() public { msg.sender.call{value:1 ether}(\"\"); } }"
}

# 6. APP GRID
col1, col2 = st.columns(2, gap="large")

with col1:
    with st.container(border=True):
        st.markdown('<div class="panel-hdr">📝 Source Code</div>', unsafe_allow_html=True)
        # Fix pill layout
        p1, p2 = st.columns(2)
        if p1.button("ERC-20 Example", key="pill1"): st.session_state.code = EXAMPLES["ERC-20"]
        if p2.button("Vulnerable Code", key="pill2"): st.session_state.code = EXAMPLES["Vulnerable"]
        
        src = st.text_area("in", value=st.session_state.get("code", ""), height=450, label_visibility="collapsed")
        
        if st.button("🔍 START SECURITY AUDIT", type="primary", key="audit_btn"):
            if not client:
                st.error("❌ SDK Client not ready. Check your secrets settings.")
            elif not src:
                st.warning("⚠️ Paste source code first.")
            else:
                with st.spinner("Analyzing on TEE..."):
                    try:
                        p = "Audit this code. Return JSON: {score, summary}"
                        r = client.llm.chat(model=og.TEE_LLM.GEMINI_2_0_FLASH, messages=[{"role":"user","content":src}], x402_settlement_mode=og.x402SettlementMode.SETTLE_BATCH)
                        st.session_state.rep = r.chat_output.get("content", "{}")
                        st.rerun()
                    except Exception as e: st.error(f"Audit failed: {e}")

with col2:
    with st.container(border=True):
        st.markdown('<div class="panel-hdr">📊 Audit Report</div>', unsafe_allow_html=True)
        if "rep" in st.session_state:
            st.write(st.session_state.rep)
        else:
            st.info("Results will appear here.")
