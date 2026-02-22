import streamlit as st
import opengradient as og
import os
import json
from web3 import Web3

# 1. Config
st.set_page_config(page_title="AI Smart Contract Auditor", page_icon="🛡️", layout="wide")

# 2. Key Handling
pk = st.secrets.get("OG_PRIVATE_KEY") or os.environ.get("OG_PRIVATE_KEY")
if pk: pk = pk.strip()

# 3. Design Restoration (Localhost Clone)
# Use a raw string for CSS to avoid any Tokenization/Python interpolation issues
CSS_RESTORE = r'''
<style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;700;800&family=JetBrains+Mono:wght@400;500;600&display=swap');

    .stApp { background: #04060d; color: #d4dff7; font-family: 'Outfit', sans-serif; }
    [data-testid="stHeader"] { visibility: hidden; }
    
    .title-box { text-align: center; padding: 30px 0 10px; }
    .title-main { 
        font-size: 3.5rem; font-weight: 800; 
        background: linear-gradient(135deg, #60a5fa 0%, #22d3ee 50%, #10b981 100%);
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;
        padding-bottom: 10px;
    }
    
    .status-bar-og {
        display: flex; justify-content: center; gap: 30px; 
        background: rgba(40, 120, 255, 0.05); border: 1px solid rgba(60, 130, 255, 0.2);
        border-radius: 12px; padding: 12px 25px; margin: 0 auto 35px; max-width: 950px;
        font-size: 0.8rem; color: #6b7fa8; backdrop-filter: blur(10px); flex-wrap: wrap;
    }
    .status-bar-og b { color: #22d3ee; font-family: 'JetBrains Mono'; }

    div[data-testid="stVerticalBlockBorderWrapper"] {
        background: rgba(10, 14, 28, 0.95) !important;
        border: 1px solid rgba(60, 130, 255, 0.25) !important;
        border-radius: 20px !important; padding: 25px !important;
        box-shadow: 0 10px 40px rgba(0,0,0,0.5) !important;
    }
    
    .stButton > button { border-radius: 10px !important; font-weight: 700 !important; }
    button[kind="primary"] {
        background: linear-gradient(135deg, #3b82f6, #22d3ee) !important;
        color: white !important; height: 3.5rem !important; width: 100% !important; border: none !important;
    }
    
    button[kind="secondary"] {
        background: rgba(255,255,255,0.05) !important; color: #6b7fa8 !important; 
        border: 1px solid rgba(255,255,255,0.1) !important; border-radius: 99px !important;
        font-size: 0.72rem !important;
    }
</style>
'''
st.markdown(CSS_RESTORE, unsafe_allow_html=True)

# 4. Global Objects (Direct Initialization)
client = None
wallet_addr = "0x00...00"
balance = "0.000"

if pk:
    try:
        if "client_obj" not in st.session_state:
            st.session_state.client_obj = og.Client(private_key=pk)
        client = st.session_state.client_obj
        
        w3 = Web3(Web3.HTTPProvider("https://sepolia.base.org"))
        acct = w3.eth.account.from_key(pk)
        wallet_addr = acct.address
        # Simplified Balance fetch
        OPG = "0x240b09731D96979f50B2C649C9CE10FcF9C7987F"
        ABI = [{"inputs":[{"name":"account","type":"address"}],"name":"balanceOf","outputs":[{"name":"","type":"uint256"}],"stateMutability":"view","type":"function"}]
        contract = w3.eth.contract(address=OPG, abi=ABI)
        balance = "{:.3f}".format(contract.functions.balanceOf(wallet_addr).call() / 1e18)
    except Exception as e:
        st.sidebar.error(f"Initialization Error: {e}")

# 5. Header Content
st.markdown('<div class="title-box"><div class="title-main">Security Auditor</div><div style="color:#6b7fa8;">TEE-Verified AI Analysis Engine</div></div>', unsafe_allow_html=True)
st.markdown(f'''
<div class="status-bar-og">
    <div>Model: <b>GEMINI_2_0_FLASH</b></div>
    <div>Wallet: <b>{wallet_addr[:8]}...{wallet_addr[-6:]}</b></div>
    <div>Balance: <b>{balance} OPG</b></div>
    <div>Network: <b>Base Sepolia</b></div>
</div>
''', unsafe_allow_html=True)

# 6. APP GRID
col1, col2 = st.columns(2, gap="large")

with col1:
    with st.container(border=True):
        st.write("### 📝 Source Code")
        c1, c2, c3 = st.columns(3)
        if c1.button("ERC-20 Example"): st.session_state.code_val = "// Example"
        if c2.button("Vulnerable Code"): st.session_state.code_val = "// Vulnerable"
        if c3.button("Reentrancy"): st.session_state.code_val = "// Reentrancy"
        
        code_in = st.text_area("in", value=st.session_state.get("code_val", ""), height=450, label_visibility="collapsed")
        
        if st.button("🔍 START SECURITY AUDIT", type="primary"):
            if client is None: st.error("❌ SDK not initialized. Please reboot the app.")
            elif not code_in: st.warning("Paste code!")
            else:
                with st.spinner("TEE Processing..."):
                    try:
                        p = "Audit this code. Return JSON: {score: number, summary: string, findings: [{title, desc}]}"
                        r = client.llm.chat(model=og.TEE_LLM.GEMINI_2_0_FLASH, messages=[{"role":"user","content":code_in}], x402_settlement_mode=og.x402SettlementMode.SETTLE_BATCH)
                        st.session_state.audit_rep = json.loads(r.chat_output.get("content", "{}"))
                        st.rerun()
                    except Exception as e: st.error(str(e))

with col2:
    with st.container(border=True):
        st.write("### 📊 Analysis Report")
        if "audit_rep" in st.session_state:
            st.write(st.session_state.audit_rep)
        else:
            st.info("System Ready. Paste code to generate report.")
