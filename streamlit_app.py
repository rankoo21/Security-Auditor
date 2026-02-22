import streamlit as st
import opengradient as og
import os
import json
from web3 import Web3

# 1. Page Config (Must be the very first)
st.set_page_config(page_title="AI Auditor", page_icon="🛡️", layout="wide")

# 2. Safe CSS Injection (Line by line to avoid TokenError)
st.markdown('<style>@import url("https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;800&family=JetBrains+Mono&display=swap");</style>', unsafe_allow_html=True)
st.markdown('<style>.stApp { background-color: #04060d; color: #d4dff7; font-family: "Outfit", sans-serif; }</style>', unsafe_allow_html=True)
st.markdown('<style>[data-testid="stHeader"] { visibility: hidden; }</style>', unsafe_allow_html=True)
st.markdown('<style>.main-title { text-align: center; font-size: 3rem; font-weight: 800; background: linear-gradient(135deg, #60a5fa, #22d3ee); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }</style>', unsafe_allow_html=True)

# 3. Initialization Logic
pk_hex = st.secrets.get("OG_PRIVATE_KEY") or os.environ.get("OG_PRIVATE_KEY")

def get_client(k):
    if not k: return None
    try: return og.Client(private_key=k)
    except: return None

og_c = get_client(pk_hex)

# Get Account Info
addr = "0x00...00"
bal = "0.00"
if pk_hex:
    try:
        w3 = Web3(Web3.HTTPProvider("https://sepolia.base.org"))
        acc = w3.eth.account.from_key(pk_hex)
        addr = acc.address
        # Simplified balance
        OPG = "0x240b09731D96979f50B2C649C9CE10FcF9C7987F"
        ABI = [{"inputs":[{"name":"account","type":"address"}],"name":"balanceOf","outputs":[{"name":"","type":"uint256"}],"stateMutability":"view","type":"function"}]
        contract = w3.eth.contract(address=OPG, abi=ABI)
        bal = round(contract.functions.balanceOf(addr).call() / 1e18, 3)
    except: pass

# 4. Header
st.markdown('<div class="main-title">AI Security Auditor</div>', unsafe_allow_html=True)
st.markdown(f'<div style="text-align:center; color:#6b7fa8; font-size:0.8rem; margin-bottom:2rem;">Wallet: {addr} | Balance: {bal} OPG</div>', unsafe_allow_html=True)

# 5. App Layout
col_a, col_b = st.columns(2)

with col_a:
    st.subheader("📝 Source Code")
    # Small Buttons
    e1, e2 = st.columns(2)
    if e1.button("Load ERC-20"):
        st.session_state.code_content = "// ERC-20 Code\npragma solidity ^0.8.0;\ncontract Token {}"
    if e2.button("Load Vulnerable"):
        st.session_state.code_content = "// Vulnerable Code\npragma solidity ^0.7.0;\ncontract Bank { function withdraw() public { msg.sender.call{value: 1 ether}(\"\"); } }"
    
    # Text Area
    u_code = st.text_area("input", value=st.session_state.get("code_content", ""), height=400, key="editor_area", label_visibility="collapsed")
    
    if st.button("🔍 SCAN NOW", use_container_width=True):
        if not og_c: st.error("SDK Initialization Failed")
        elif not u_code: st.warning("Please enter code")
        else:
            with st.spinner("Analyzing on TEE..."):
                try:
                    p = "Audit the following code. Return JSON format: {score: number, summary: string, vulnerabilities: [{title: string, desc: string}]}"
                    m = [{"role":"system","content":p}, {"role":"user","content":u_code}]
                    r = og_c.llm.chat(model=og.TEE_LLM.GEMINI_2_0_FLASH, messages=m, x402_settlement_mode=og.x402SettlementMode.SETTLE_BATCH)
                    raw_res = r.chat_output.get("content", "")
                    if "```json" in raw_res: raw_res = raw_res.split("```json")[1].split("```")[0]
                    st.session_state.scan_result = json.loads(raw_res)
                    st.rerun()
                except Exception as ex: st.error(str(ex))

with col_b:
    st.subheader("📊 Audit Report")
    if "scan_result" in st.session_state:
        res = st.session_state.scan_result
        st.metric("Risk Score", res.get("score" if "score" in res else "risk_score", 0))
        st.write(res.get("summary", ""))
        for v in res.get("vulnerabilities", []):
            with st.expander(f"⚠️ {v.get('title')}"):
                st.write(v.get("desc" if "desc" in v else "description"))
    else:
        st.info("Results will appear here after scanning.")
