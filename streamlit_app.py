import streamlit as st
import opengradient as og
import os
import json
import time
from web3 import Web3

# Page config
st.set_page_config(page_title="AI Smart Contract Auditor", page_icon="🛡️", layout="wide")

# Custom CSS for premium look
st.markdown("""
    <style>
    .main { background-color: #04060d; color: #d4dff7; }
    .stButton>button {
        background: linear-gradient(135deg, #3b82f6, #22d3ee);
        color: white; border: none; font-weight: bold;
        border-radius: 8px; width: 100%; height: 3em;
    }
    .stTextArea>div>div>textarea { background-color: #080c18; color: #d4dff7; font-family: 'JetBrains Mono', monospace; }
    </style>
""", unsafe_allow_html=True)

# App Title
st.title("🛡️ AI Smart Contract Auditor")
st.markdown("Powered by **OpenGradient Trusted Execution Environment (TEE)**")

# Sidebar for Wallet Info
with st.sidebar:
    st.header("🔗 System Info")
    
    # Safer secret retrieval
    try:
        if "OG_PRIVATE_KEY" in st.secrets:
            pk = st.secrets["OG_PRIVATE_KEY"]
        else:
            pk = os.environ.get("OG_PRIVATE_KEY")
    except:
        pk = None
    
    if not pk:
        st.error("🔑 **OG_PRIVATE_KEY** not found!")
        st.info("Go to **App Settings > Secrets** and add: `OG_PRIVATE_KEY = 'your_key_here'`")
        st.stop()
        
    try:
        w3 = Web3(Web3.HTTPProvider("https://sepolia.base.org"))
        acct = w3.eth.account.from_key(pk)
        st.info(f"Wallet: `{acct.address[:6]}...{acct.address[-4:]}`")
        
        client = og.Client(private_key=pk)
        st.success("OpenGradient Client Connected")
    except Exception as e:
        st.error(f"Error: {e}")
        st.stop()

# Layout
col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("📝 Source Code")
    code = st.text_area("Paste Solidity Code Here:", height=400, placeholder="pragma solidity ^0.8.0; ...")
    
    if st.button("🔍 Start Security Audit"):
        if not code:
            st.warning("Please enter code first!")
        else:
            with st.spinner("Analyzing vulnerabilities via TEE LLM..."):
                try:
                    # Prepare messages
                    system_prompt = """Analyze Solidity. Return JSON ONLY.
                    {
                      "summary": "1-2 sentence overview",
                      "risk_score": 0-100,
                      "vulnerabilities": [{"title": "Name", "severity": "High", "description": "...", "recommendation": "..."}]
                    }"""
                    
                    messages = [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": f"Audit this:\n\n{code}"}
                    ]
                    
                    # Call OPG SDK
                    result = client.llm.chat(
                        model=og.TEE_LLM.GEMINI_2_0_FLASH,
                        messages=messages,
                        max_tokens=1000,
                        x402_settlement_mode=og.x402SettlementMode.SETTLE_BATCH
                    )
                    
                    # Parse result
                    raw = (result.chat_output or {}).get("content", "")
                    # Simple JSON cleanup for markdown blocks
                    if "```json" in raw: raw = raw.split("```json")[1].split("```")[0]
                    elif "```" in raw: raw = raw.split("```")[1].split("```")[0]
                    
                    audit_data = json.loads(raw)
                    st.session_state.audit_result = audit_data
                    st.session_state.payment_hash = getattr(result, "payment_hash", None)
                    
                except Exception as e:
                    st.error(f"Audit Failed: {e}")

with col2:
    st.subheader("📊 Audit Report")
    
    if "audit_result" in st.session_state:
        res = st.session_state.audit_result
        
        # Risk Score
        score = res.get("risk_score", 0)
        color = "red" if score > 70 else "orange" if score > 30 else "green"
        st.markdown(f"### Risk Score: <span style='color:{color}'>{score}/100</span>", unsafe_allow_html=True)
        
        st.write(f"**Summary:** {res.get('summary', '')}")
        
        # Vulnerabilities
        st.markdown("#### Findings")
        for v in res.get("vulnerabilities", []):
            with st.expander(f"[{v.get('severity', 'Info')}] {v.get('title', 'Vuln')}"):
                st.write(f"**Description:** {v.get('description', '')}")
                st.write(f"**Fix:** {v.get('recommendation', '')}")
                
        # Settlement
        if st.session_state.payment_hash:
            st.success(f"Verified on-chain! Tx: {st.session_state.payment_hash[:12]}...")
            st.link_button("View on Basescan", f"https://sepolia.basescan.org/tx/{st.session_state.payment_hash}")
    else:
        st.info("Results will appear here after analysis.")
