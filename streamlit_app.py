import streamlit as st
import opengradient as og
import os
import json
from web3 import Web3

# 1. Config
st.set_page_config(page_title="AI Auditor", page_icon="🛡️", layout="wide")

# 2. Key Handling
# We use a very direct approach to avoid any confusion
pk = None
if "OG_PRIVATE_KEY" in st.secrets:
    pk = st.secrets["OG_PRIVATE_KEY"]
elif os.environ.get("OG_PRIVATE_KEY"):
    pk = os.environ.get("OG_PRIVATE_KEY")

# 3. Style (Using a variable to be safe)
CSS = r"""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;800&family=JetBrains+Mono&display=swap');
    .stApp { background: #04060d; color: #d4dff7; font-family: 'Outfit', sans-serif; }
    [data-testid="stHeader"] { visibility: hidden; }
    .main-title { text-align: center; padding: 20px 0; font-size: 3rem; font-weight: 800; background: linear-gradient(135deg, #60a5fa, #22d3ee, #10b981); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
    .info-bar { background: rgba(255,255,255,0.03); border: 1px solid rgba(255,255,255,0.1); border-radius: 12px; padding: 12px; margin-bottom: 30px; display: flex; justify-content: center; gap: 30px; font-size: 0.8rem; color: #6b7fa8; }
    .info-bar b { color: #22d3ee; }
    div[data-testid="stVerticalBlockBorderWrapper"] { background: rgba(10, 14, 28, 0.9) !important; border: 1px solid rgba(60, 130, 255, 0.2) !important; border-radius: 20px !important; }
</style>
"""
st.markdown(CSS, unsafe_allow_html=True)

# 4. Wallet Info
w_addr = "0x000...000"
balance = "0.00"
client = None

if pk:
    try:
        client = og.Client(private_key=pk)
        w3 = Web3(Web3.HTTPProvider("https://sepolia.base.org"))
        acct = w3.eth.account.from_key(pk)
        w_addr = acct.address
        # RPC call for balance
        OPG_ADDR = "0x240b09731D96979f50B2C649C9CE10FcF9C7987F"
        ABI = [{"inputs":[{"name":"account","type":"address"}],"name":"balanceOf","outputs":[{"name":"","type":"uint256"}],"stateMutability":"view","type":"function"}]
        contract = w3.eth.contract(address=OPG_ADDR, abi=ABI)
        raw_bal = contract.functions.balanceOf(w_addr).call()
        balance = round(raw_bal / 1e18, 3)
    except Exception as e:
        st.sidebar.error(f"Logic Error: {e}")
else:
    st.error("🔑 Private Key missing! Add 'OG_PRIVATE_KEY' to Streamlit Secrets.")

# 5. UI Layout
st.markdown('<div class="main-title">Security Auditor</div>', unsafe_allow_html=True)
st.markdown(f'<div class="info-bar">Wallet: <b>{w_addr}</b> | Balance: <b>{balance} OPG</b></div>', unsafe_allow_html=True)

col1, col2 = st.columns(2, gap="large")

with col1:
    with st.container(border=True):
        st.subheader("📝 Source Code")
        if st.button("Load Vulnerable Example"):
            st.session_state.code = "// Example\npragma solidity ^0.7.0;\ncontract Vault { function withdraw() public { msg.sender.call{value:1 ether}(\"\"); } }"
        
        user_code = st.text_area("c", value=st.session_state.get("code", ""), height=400, label_visibility="collapsed")
        
        if st.button("🔍 START SCAN", type="primary"):
            if not client: st.error("Client not ready")
            elif not user_code: st.warning("Paste code")
            else:
                with st.spinner("TEE Analysis..."):
                    try:
                        p = "Audit this. Return JSON {score: number, summary: string}"
                        res = client.llm.chat(model=og.TEE_LLM.GEMINI_2_0_FLASH, messages=[{"role":"user","content":user_code}])
                        st.session_state.report = res.chat_output.get("content", "{}")
                        st.rerun()
                    except Exception as e: st.error(str(e))

with col2:
    with st.container(border=True):
        st.subheader("📊 Report")
        if "report" in st.session_state:
            st.code(st.session_state.report)
        else:
            st.info("Report will appear here.")
