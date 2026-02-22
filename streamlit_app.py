import streamlit as st
import opengradient as og
import os
import json
from web3 import Web3

# 1. Page Config (Must be the very first line)
st.set_page_config(page_title="AI Security Auditor", page_icon="🛡️", layout="wide")

# 2. Key Handling (Direct & Stable)
pk = st.secrets.get("OG_PRIVATE_KEY") or os.environ.get("OG_PRIVATE_KEY")
if pk:
    pk = pk.strip()
    if not pk.startswith("0x") and len(pk) == 64:
        pk = "0x" + pk

# 3. CSS Injection (Pure Localhost Look)
# We avoid f-strings here to bypass the Tokenizer error
CSS = """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;700;800&family=JetBrains+Mono&display=swap');

    .stApp { background: #04060d; color: #d4dff7; font-family: 'Outfit', sans-serif; }
    [data-testid="stHeader"] { visibility: hidden; }
    
    /* Header & Title */
    .title-area { text-align: center; padding: 30px 0; }
    .main-title { 
        font-size: 3.5rem; font-weight: 800; 
        background: linear-gradient(135deg, #60a5fa, #22d3ee, #10b981);
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;
    }
    .sub-title { color: #6b7fa8; font-size: 1rem; margin-top: 5px; }

    /* Info Bar (The Localhost Status Bar) */
    .info-bar {
        background: rgba(255,255,255,0.03); border: 1px solid rgba(255,255,255,0.08);
        border-radius: 12px; padding: 12px 25px; margin: 0 auto 30px; display: flex; 
        justify-content: center; gap: 30px; font-size: 0.8rem; color: #6b7fa8; max-width: 900px;
    }
    .info-bar b { color: #22d3ee; font-family: 'JetBrains Mono'; }

    /* Panels (Native-like containers) */
    [data-testid="stVerticalBlockBorderWrapper"] {
        background: rgba(10, 14, 28, 0.95) !important;
        border: 1px solid rgba(60, 130, 255, 0.2) !important;
        border-radius: 20px !important;
        padding: 20px !important;
    }
    
    .panel-hdr { font-weight: 700; font-size: 1.1rem; color: #fff; margin-bottom: 20px; }

    /* Inputs & Buttons */
    div[data-baseweb="textarea"] { background: #080c18 !important; border: 1px solid rgba(255,255,255,0.1) !important; border-radius: 12px !important; }
    textarea { color: #d4dff7 !important; font-family: 'JetBrains Mono' !important; font-size: 0.85rem !important; }
    
    .stButton > button[kind="primary"] {
        background: linear-gradient(135deg, #3b82f6, #22d3ee) !important;
        color: white !important; font-weight: 800 !important; border: none !important;
        height: 3.5rem !important; width: 100% !important; border-radius: 12px !important;
        box-shadow: 0 4px 20px rgba(59, 130, 246, 0.4) !important;
    }
    
    .pills button {
        background: rgba(255,255,255,0.05) !important; color: #6b7fa8 !important;
        border-radius: 99px !important; border: 1px solid rgba(255,255,255,0.1) !important;
        font-size: 0.72rem !important; padding: 4px 15px !important;
    }
</style>
"""
st.markdown(CSS, unsafe_allow_html=True)

# 4. Global Variables & SDK Init
client = None
wallet_addr = "0x00...00"
balance = "0.00"

if pk:
    try:
        # Initializing SDK directly to avoid cache issues
        client = og.Client(private_key=pk)
        w3 = Web3(Web3.HTTPProvider("https://sepolia.base.org"))
        acct = w3.eth.account.from_key(pk)
        wallet_addr = acct.address
        # Simplified Balance fetch
        OPG = "0x240b09731D96979f50B2C649C9CE10FcF9C7987F"
        ABI = [{"inputs":[{"name":"account","type":"address"}],"name":"balanceOf","outputs":[{"name":"","type":"uint256"}],"stateMutability":"view","type":"function"}]
        c = w3.eth.contract(address=OPG, abi=ABI)
        balance = round(c.functions.balanceOf(wallet_addr).call() / 1e18, 3)
    except Exception as e:
        st.sidebar.error(f"Init Error: {e}")
else:
    st.error("🔑 Private Key missing in Secrets!")

# 5. Header Content
st.markdown('<div class="title-area"><div class="main-title">Security Auditor</div><div class="sub-title">TEE-Verified AI Smart Contract Audit</div></div>', unsafe_allow_html=True)
st.markdown(f'''
<div class="info-bar">
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
        st.markdown('<div class="panel-hdr">📝 Source Code</div>', unsafe_allow_html=True)
        
        # Example Buttons
        st.markdown('<div class="pills">', unsafe_allow_html=True)
        p1, p2, p3 = st.columns(3)
        if p1.button("ERC-20 Example", key="btn1"): st.session_state.code = "// ERC-20 Code Sample\npragma solidity ^0.8.0;\ncontract Token { }"
        if p2.button("Vulnerable Code", key="btn2"): st.session_state.code = "// Vulnerable Code Sample\npragma solidity ^0.7.0;\ncontract Bank { function pull() public { msg.sender.call{value:1 ether}(\"\"); } }"
        if p3.button("Reentrancy", key="btn3"): st.session_state.code = "// Reentrancy Sample\npragma solidity ^0.8.0;\ncontract Vault { }"
        st.markdown('</div>', unsafe_allow_html=True)
        
        code_input = st.text_area("in", value=st.session_state.get("code", ""), height=450, label_visibility="collapsed")
        
        if st.button("🔍 START SECURITY ANALYSIS", type="primary"):
            if client is None:
                st.error("SDK not initialized. Check your Private Key.")
            elif not code_input:
                st.warning("Paste code first.")
            else:
                with st.spinner("Analyzing on TEE..."):
                    try:
                        p = "Audit this code. Return JSON: {score, summary, findings:[{title, desc}]}"
                        r = client.llm.chat(model=og.TEE_LLM.GEMINI_2_0_FLASH, messages=[{"role":"user","content":code_input}], x402_settlement_mode=og.x402SettlementMode.SETTLE_BATCH)
                        raw = r.chat_output.get("content", "")
                        if "```json" in raw: raw = raw.split("```json")[1].split("```")[0]
                        st.session_state.report = json.loads(raw)
                        st.session_state.tx = getattr(r, "payment_hash", None)
                        st.rerun()
                    except Exception as e:
                        st.error(f"Audit Error: {e}")

with col2:
    with st.container(border=True):
        st.markdown('<div class="panel-hdr">📊 Analysis Report</div>', unsafe_allow_html=True)
        if "report" in st.session_state:
            rep = st.session_state.report
            sc = int(rep.get("score", 0))
            cl = "#ef4444" if sc > 70 else "#f97316" if sc > 40 else "#10b981"
            
            st.markdown(f'''
                <div style="background:rgba(0,0,0,0.2); border-radius:15px; padding:30px; text-align:center; border:1px solid rgba(255,255,255,0.05);">
                    <div style="font-size:0.8rem; color:#6b7fa8;">SECURITY RISK SCORE</div>
                    <div style="font-size:4.5rem; font-weight:800; color:{cl};">{sc}</div>
                    <p style="margin-top:20px;">{rep.get('summary', '')}</p>
                </div>
            ''', unsafe_allow_html=True)
            
            for f in rep.get("findings", []):
                with st.expander(f"⚠️ {f.get('title')}"):
                    st.write(f.get('desc'))
            
            if st.session_state.get("tx"):
                st.markdown(f'<div style="text-align:center; margin-top:20px;"><a href="https://sepolia.basescan.org/tx/{st.session_state.tx}" target="_blank" style="color:#22d3ee; text-decoration:none;">🔗 View On-Chain Proof</a></div>', unsafe_allow_html=True)
        else:
            st.info("Results will appear here after analysis.")
