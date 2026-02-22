import streamlit as st
import opengradient as og
import os
import json
from web3 import Web3

# VERSION 3.0 - STABLE RELEASE
st.set_page_config(page_title="Security Auditor AI", page_icon="🛡️", layout="wide")

# 1. CSS Injection (Clean & No Token Issues)
st.markdown('''
<style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;800&family=JetBrains+Mono&display=swap');
    .stApp { background-color: #04060d; color: #d4dff7; font-family: 'Outfit', sans-serif; }
    [data-testid="stHeader"] { visibility: hidden; }
    .main-title {
        text-align: center; font-size: 3.5rem; font-weight: 800;
        background: linear-gradient(135deg, #60a5fa 0%, #22d3ee 50%, #10b981 100%);
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;
        padding: 30px 0 10px;
    }
    .status-bar {
        display: flex; justify-content: center; gap: 30px; 
        background: rgba(255,255,255,0.03); border: 1px solid rgba(255,255,255,0.1);
        border-radius: 12px; padding: 12px; margin: 0 auto 30px; max-width: 850px;
        font-size: 0.8rem; color: #6b7fa8;
    }
    .status-bar b { color: #22d3ee; }
    [data-testid="stVerticalBlockBorderWrapper"] {
        background: rgba(10, 14, 28, 0.9) !important;
        border: 1px solid rgba(60, 130, 255, 0.2) !important;
        border-radius: 20px !important;
    }
    textarea { font-family: 'JetBrains Mono' !important; font-size: 0.85rem !important; }
    .stButton > button[kind="primary"] {
        background: linear-gradient(135deg, #3b82f6, #22d3ee) !important;
        width: 100% !important; border: none !important; height: 3.5rem !important;
        font-weight: 800 !important; font-size: 1.1rem !important;
    }
</style>
''', unsafe_allow_html=True)

# 2. Key & Client
pk_key = st.secrets.get("OG_PRIVATE_KEY") or os.environ.get("OG_PRIVATE_KEY")

@st.cache_resource
def load_og_client(k):
    if not k: return None
    try: return og.Client(private_key=k)
    except: return None

client_og = load_og_client(pk_key)

# 3. Web3 Info
w_addr = "0x00...00"
w_bal = "0.00"
if pk_key:
    try:
        w3 = Web3(Web3.HTTPProvider("https://sepolia.base.org"))
        acc = w3.eth.account.from_key(pk_key)
        w_addr = acc.address
        OPG = "0x240b09731D96979f50B2C649C9CE10FcF9C7987F"
        ABI = [{"inputs":[{"name":"account","type":"address"}],"name":"balanceOf","outputs":[{"name":"","type":"uint256"}],"stateMutability":"view","type":"function"}]
        contract = w3.eth.contract(address=OPG, abi=ABI)
        w_bal = round(contract.functions.balanceOf(w_addr).call() / 1e18, 3)
    except: pass

# 4. Header
st.markdown('<div class="main-title">Security Auditor</div>', unsafe_allow_html=True)
st.markdown(f'<div class="status-bar"><b>VERSION 3.0</b> | Wallet: <b>{w_addr[:6]}...{w_addr[-4:]}</b> | Balance: <b>{w_bal} OPG</b></div>', unsafe_allow_html=True)

# 5. App Grid
left_col, right_col = st.columns(2, gap="large")

with left_col:
    with st.container(border=True):
        st.write("### 📝 Smart Contract Source")
        
        # Example Buttons
        btn_c1, btn_c2 = st.columns(2)
        if btn_c1.button("Load ERC-20"):
            st.session_state.code_ed = '// SPDX-License-Identifier: MIT\npragma solidity ^0.8.0;\ncontract MyToken {}'
        if btn_c2.button("Load Vulnerable"):
            st.session_state.code_ed = '// Vulnerable Contract\npragma solidity ^0.7.0;\ncontract Vault {\n    function withdraw() public {\n        msg.sender.call{value: 1 ether}("");\n    }\n}'
            
        code_val = st.text_area("source", value=st.session_state.get("code_ed", ""), height=400, key="editor", label_visibility="collapsed")
        
        if st.button("🔍 START SECURITY AUDIT", type="primary"):
            if not client_og: st.error("SDK Error")
            elif not code_val: st.warning("Empty code")
            else:
                with st.spinner("Analyzing on OpenGradient TEE..."):
                    try:
                        p = "Audit this. Return JSON {score, summary, findings:[{title, desc}]}"
                        r = client_og.llm.chat(
                            model=og.TEE_LLM.GEMINI_2_0_FLASH,
                            messages=[{"role":"system","content":p}, {"role":"user","content":code_val}],
                            x402_settlement_mode=og.x402SettlementMode.SETTLE_BATCH
                        )
                        raw = r.chat_output.get("content", "")
                        if "```json" in raw: raw = raw.split("```json")[1].split("```")[0]
                        st.session_state.audit_report = json.loads(raw)
                        st.session_state.audit_txid = getattr(r, "payment_hash", None)
                        st.rerun()
                    except Exception as e: st.error(str(e))

with right_col:
    with st.container(border=True):
        st.write("### 📊 Report Findings")
        if "audit_report" in st.session_state:
            rep = st.session_state.audit_report
            st.metric("Risk Score", rep.get('score', 0))
            st.write(rep.get('summary', ''))
            for f in rep.get('findings', []):
                with st.expander(f.get('title')):
                    st.write(f.get('desc'))
            if st.session_state.get("audit_txid"):
                st.markdown(f'[View On-Chain Proof](https://sepolia.basescan.org/tx/{st.session_state.audit_txid})')
        else:
            st.info("Paste code and click Start to generate analysis.")
