import streamlit as st
import opengradient as og
import os
import json
from web3 import Web3

# 1. Page Config
st.set_page_config(page_title="AI Smart Contract Auditor", page_icon="🛡️", layout="wide")

# 2. Key & Logic Initialization
pk = st.secrets.get("OG_PRIVATE_KEY") or os.environ.get("OG_PRIVATE_KEY")
if pk:
    pk = pk.strip()
    if not pk.startswith("0x") and len(pk) == 64: pk = "0x" + pk

# 3. Safe CSS Injection (Line by line to avoid TokenError)
st.markdown('<style>@import url("https://fonts.googleapis.com/css2?family=Outfit:wght@400;700;800&family=JetBrains+Mono&display=swap");</style>', unsafe_allow_html=True)
st.markdown('<style>body, .stApp { background-color: #04060d; color: #d4dff7; font-family: "Outfit", sans-serif; }</style>', unsafe_allow_html=True)
st.markdown('<style>[data-testid="stHeader"] { visibility: hidden; }</style>', unsafe_allow_html=True)
st.markdown('<style>.title-grad { text-align: center; font-size: 3rem; font-weight: 800; background: linear-gradient(135deg, #60a5fa, #22d3ee, #10b981); -webkit-background-clip: text; -webkit-text-fill-color: transparent; margin-bottom: 20px; }</style>', unsafe_allow_html=True)
st.markdown('<style>.status-box { background: rgba(255,255,255,0.03); border: 1px solid rgba(255,255,255,0.1); border-radius: 12px; padding: 12px; margin: 0 auto 30px; display: flex; justify-content: center; gap: 30px; font-size: 0.8rem; color: #6b7fa8; max-width: 900px; }</style>', unsafe_allow_html=True)
st.markdown('<style>div[data-testid="stVerticalBlockBorderWrapper"] { background: rgba(10, 14, 28, 0.9) !important; border: 1px solid rgba(60, 130, 255, 0.2) !important; border-radius: 20px !important; }</style>', unsafe_allow_html=True)

# 4. Global Variables
wa = "0x00...00"
wb = "0.00"
client = None

if pk:
    try:
        client = og.Client(private_key=pk)
        w3 = Web3(Web3.HTTPProvider("https://sepolia.base.org"))
        acct = w3.eth.account.from_key(pk)
        wa = acct.address
        # Balance
        OPG = "0x240b09731D96979f50B2C649C9CE10FcF9C7987F"
        ABI = [{"inputs":[{"name":"account","type":"address"}],"name":"balanceOf","outputs":[{"name":"","type":"uint256"}],"stateMutability":"view","type":"function"}]
        contract = w3.eth.contract(address=OPG, abi=ABI)
        wb = round(contract.functions.balanceOf(wa).call() / 1e18, 3)
    except Exception as e:
        st.sidebar.error(f"Init Error: {e}")

# 5. Header UI
st.markdown('<div class="title-grad">Security Auditor AI</div>', unsafe_allow_html=True)
st.markdown(f'<div class="status-box">Wallet: <b>{wa}</b> | Balance: <b>{wb} OPG</b></div>', unsafe_allow_html=True)

# 6. Content Grid
c1, c2 = st.columns(2, gap="large")

with c1:
    with st.container(border=True):
        st.subheader("📝 Source Code")
        if st.button("Load ERC-20"):
            st.session_state.code = "// ERC-20 Example\npragma solidity ^0.8.0;\ncontract Token { }"
        
        u_code = st.text_area("input", value=st.session_state.get("code", ""), height=400, label_visibility="collapsed")
        
        if st.button("🔍 SCAN SMART CONTRACT", type="primary"):
            if not client: st.error("SDK Error: Check Private Key")
            elif not u_code: st.warning("Paste code")
            else:
                with st.spinner("Analyzing on TEE..."):
                    try:
                        resp = client.llm.chat(model=og.TEE_LLM.GEMINI_2_0_FLASH, messages=[{"role":"user","content":u_code}])
                        st.session_state.rep = resp.chat_output.get("content", "Error parsing output")
                        st.rerun()
                    except Exception as e: st.error(str(e))

with c2:
    with st.container(border=True):
        st.subheader("📊 Security Report")
        if "rep" in st.session_state:
            st.markdown(f"```json\n{st.session_state.rep}\n```")
        else:
            st.info("Results will appear here.")
