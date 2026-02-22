import streamlit as st
import opengradient as og
import os
import json
from web3 import Web3

# Version 2.1 - Ultra Stable Build
st.set_page_config(page_title="Security Auditor AI", page_icon="🛡️", layout="wide")

# --- CUSTOM THEME ---
# Using simple strings to avoid any f-string tokenization issues
css_code = """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;800&family=JetBrains+Mono&display=swap');
    .stApp { background-color: #04060d; color: #d4dff7; font-family: 'Outfit', sans-serif; }
    [data-testid="stHeader"] { visibility: hidden; }
    .title-gradient {
        text-align: center; font-size: 3.5rem; font-weight: 800;
        background: linear-gradient(135deg, #60a5fa 0%, #22d3ee 50%, #10b981 100%);
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;
        padding: 20px 0;
    }
    .status-box {
        display: flex; justify-content: center; gap: 30px; 
        background: rgba(255,255,255,0.03); border: 1px solid rgba(255,255,255,0.1);
        border-radius: 12px; padding: 12px; margin: 0 auto 30px; max-width: 800px;
        font-size: 0.8rem; color: #6b7fa8;
    }
    .status-box b { color: #22d3ee; }
    [data-testid="stVerticalBlockBorderWrapper"] {
        background: rgba(10, 14, 28, 0.9) !important;
        border: 1px solid rgba(60, 130, 255, 0.2) !important;
        border-radius: 20px !important;
    }
    textarea { font-family: 'JetBrains Mono' !important; font-size: 0.85rem !important; }
</style>
"""
st.markdown(css_code, unsafe_allow_html=True)

# --- CORE LOGIC ---
og_key = st.secrets.get("OG_PRIVATE_KEY") or os.environ.get("OG_PRIVATE_KEY")

def create_client(k):
    if not k: return None
    try: return og.Client(private_key=k)
    except: return None

og_client = create_client(og_key)

w_addr = "0x00...00"
w_bal = "0.00"
if og_key:
    try:
        w3_conn = Web3(Web3.HTTPProvider("https://sepolia.base.org"))
        acct_obj = w3_conn.eth.account.from_key(og_key)
        w_addr = acct_obj.address
        # Token Check
        OPG = "0x240b09731D96979f50B2C649C9CE10FcF9C7987F"
        ABI = [{"inputs":[{"name":"account","type":"address"}],"name":"balanceOf","outputs":[{"name":"","type":"uint256"}],"stateMutability":"view","type":"function"}]
        contract = w3_conn.eth.contract(address=OPG, abi=ABI)
        w_bal = round(contract.functions.balanceOf(w_addr).call() / 1e18, 3)
    except: pass

# --- UI HEADER ---
st.markdown('<div class="title-gradient">Security Auditor</div>', unsafe_allow_html=True)
st.markdown(f'<div class="status-box">Model: <b>GEMINI_2_0_FLASH</b> | Wallet: <b>{w_addr[:6]}...{w_addr[-4:]}</b> | Balance: <b>{w_bal} OPG</b></div>', unsafe_allow_html=True)

# --- APP ---
main_col1, main_col2 = st.columns(2, gap="large")

with main_col1:
    with st.container(border=True):
        st.write("### 📝 Source Code")
        # Direct loading to avoid session state sync issues
        load_erc = st.button("Load ERC-20 Example")
        load_vuln = st.button("Load Vulnerable Example")
        
        ex_code = ""
        if load_erc: ex_code = "// ERC-20 Example\npragma solidity ^0.8.0;\ncontract MyToken {}"
        if load_vuln: ex_code = "// Vulnerable\npragma solidity ^0.7.0;\ncontract Vault { function withdraw() public { msg.sender.call{value:1 ether}(""); } }"
        
        source = st.text_area("code_input", value=ex_code, height=400, label_visibility="collapsed")
        
        if st.button("🔍 START ANALYSIS", type="primary"):
            if not og_client: st.error("SDK Client Error")
            elif not source: st.warning("No code provided")
            else:
                with st.spinner("TEE Processing..."):
                    try:
                        prompt = "Audit this. Return JSON {score, summary, findings:[{title, desc}]}"
                        resp = og_client.llm.chat(
                            model=og.TEE_LLM.GEMINI_2_0_FLASH,
                            messages=[{"role":"system","content":prompt}, {"role":"user","content":source}],
                            x402_settlement_mode=og.x402SettlementMode.SETTLE_BATCH
                        )
                        raw_json = resp.chat_output.get("content", "")
                        if "```json" in raw_json: raw_json = raw_json.split("```json")[1].split("```")[0]
                        st.session_state.final_rep = json.loads(raw_json)
                        st.rerun()
                    except Exception as e: st.error(str(e))

with main_col2:
    with st.container(border=True):
        st.write("### 📊 Report")
        if "final_rep" in st.session_state:
            res = st.session_state.final_rep
            st.success(f"Audit Complete! Score: {res.get('score', 0)}")
            st.write(res.get('summary', ''))
            for f in res.get('findings', []):
                with st.expander(f.get('title')):
                    st.write(f.get('desc'))
        else:
            st.info("System Ready for Audit")
