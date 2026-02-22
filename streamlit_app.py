import streamlit as st
import opengradient as og
import os
import json
from web3 import Web3

# 1. Essential Config
st.set_page_config(page_title="Security Auditor", page_icon="🛡️", layout="wide")

# 2. Ultra-Safe CSS (No Interpolation, No Token Issues)
CSS = r'''
<style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;800&family=JetBrains+Mono&display=swap');
    .stApp { background: #04060d; color: #d4dff7; font-family: 'Outfit', sans-serif; }
    [data-testid="stHeader"] { visibility: hidden; }
    .title-banner { text-align: center; padding: 35px 0 10px; }
    .title-gradient { font-size: 3.5rem; font-weight: 800; background: linear-gradient(135deg, #60a5fa, #22d3ee, #10b981); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
    .status-bar { border: 1px solid rgba(60, 130, 255, 0.2); background: rgba(255,255,255,0.03); border-radius: 12px; padding: 12px; margin: 15px auto 35px; max-width: 900px; display: flex; justify-content: center; gap: 30px; font-size: 0.8rem; color: #6b7fa8; }
    .status-bar b { color: #22d3ee; }
    div[data-testid="stVerticalBlockBorderWrapper"] { background: rgba(10, 14, 28, 0.95) !important; border: 1px solid rgba(60, 130, 255, 0.25) !important; border-radius: 20px !important; }
    button[kind="primary"] { background: linear-gradient(135deg, #3b82f6, #22d3ee) !important; border: none !important; height: 3.5rem !important; width: 100% !important; font-weight: 800 !important; color: white !important; box-shadow: 0 4px 20px rgba(59, 130, 246, 0.4) !important; }
</style>
'''
st.markdown(CSS, unsafe_allow_html=True)

# 3. Secure Key Fetching
pk = st.secrets.get("OG_PRIVATE_KEY") or os.environ.get("OG_PRIVATE_KEY")
if pk: pk = pk.strip()

# 4. Wallet Info Fetching
wallet_address = "0x00...00"
wallet_balance = "0.00"

if pk:
    try:
        w3 = Web3(Web3.HTTPProvider("https://sepolia.base.org"))
        acc = w3.eth.account.from_key(pk)
        wallet_address = acc.address
        OPG = "0x240b09731D96979f50B2C649C9CE10FcF9C7987F"
        ABI = [{"inputs":[{"name":"account","type":"address"}],"name":"balanceOf","outputs":[{"name":"","type":"uint256"}],"stateMutability":"view","type":"function"}]
        contract = w3.eth.contract(address=OPG, abi=ABI)
        wallet_balance = round(contract.functions.balanceOf(wallet_address).call() / 1e18, 3)
    except Exception as e:
        st.sidebar.error(f"Chain Error: {e}")

# 5. Header Content
st.markdown('<div class="title-banner"><div class="title-gradient">Security Auditor</div></div>', unsafe_allow_html=True)
st.markdown(f'<div class="status-bar">Wallet: <b>{wallet_address}</b> | Balance: <b>{wallet_balance} OPG</b></div>', unsafe_allow_html=True)

# 6. Main App Grid
c1, c2 = st.columns(2, gap="large")

with c1:
    with st.container(border=True):
        st.write("### 📝 Source Code")
        # Direct Loaders
        if st.button("Load ERC-20 Example"): st.session_state.code_ed = "// ERC-20 Demo\npragma solidity ^0.8.0;\ncontract Token { }"
        if st.button("Load Vulnerable Code"): st.session_state.code_ed = "// Vulnerability Demo\npragma solidity ^0.7.0;\ncontract Bank { function pay() public { msg.sender.call{value: 1 ether}(\"\"); } }"
        
        user_input = st.text_area("in", value=st.session_state.get("code_ed", ""), height=400, label_visibility="collapsed")
        
        if st.button("🔍 START SCAN", type="primary"):
            if not pk:
                st.error("🔑 Private Key missing in Secrets!")
            elif not user_input:
                st.warning("Paste code!")
            else:
                with st.spinner("TEE Analysis..."):
                    try:
                        # Init client inside the button to ensure it's alive
                        client = og.Client(private_key=pk)
                        p_sys = "Audit this. Return JSON {score, summary}"
                        r = client.llm.chat(model=og.TEE_LLM.GEMINI_2_0_FLASH, messages=[{"role":"user","content":user_input}])
                        st.session_state.audit_res = r.chat_output.get("content", "{}")
                        st.rerun()
                    except Exception as ex:
                        st.error(f"Error: {ex}")

with c2:
    with st.container(border=True):
        st.write("### 📊 Report")
        if "audit_res" in st.session_state:
            st.code(st.session_state.audit_res, language="json")
        else:
            st.info("Results will appear here.")
