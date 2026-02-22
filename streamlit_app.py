import streamlit as st
import opengradient as og
import os
import json
import time
import hashlib
from web3 import Web3

# Page setup
st.set_page_config(page_title="AI Smart Contract Auditor", page_icon="🛡️", layout="wide")

# Get PK from secrets
pk = st.secrets.get("OG_PRIVATE_KEY") or os.environ.get("OG_PRIVATE_KEY")

# Initialize Web3 & OPG
if pk:
    try:
        w3 = Web3(Web3.HTTPProvider("https://sepolia.base.org"))
        acct = w3.eth.account.from_key(pk)
        client = og.Client(private_key=pk)
        
        # Simple balance check
        OPG_TOKEN = "0x240b09731D96979f50B2C649C9CE10FcF9C7987F"
        ERC20_ABI = [{"inputs":[{"name":"account","type":"address"}],"name":"balanceOf","outputs":[{"name":"","type":"uint256"}],"stateMutability":"view","type":"function"}]
        token = w3.eth.contract(address=OPG_TOKEN, abi=ERC20_ABI)
        raw_bal = token.functions.balanceOf(acct.address).call()
        balance = round(raw_bal / 1e18, 3)
    except:
        balance = "0.00"
        acct = None
else:
    st.error("Missing OG_PRIVATE_KEY")
    st.stop()

# ─── UI Rendering (Mirroring the Original Design) ───
st.markdown(f"""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;800&family=JetBrains+Mono&display=swap');
    
    .stApp {{ background: #04060d; color: #d4dff7; font-family: 'Outfit', sans-serif; }}
    [data-testid="stHeader"] {{ background: transparent; }}
    
    .header-center {{ text-align: center; margin-bottom: 2rem; }}
    .badge {{ background: rgba(34, 211, 238, 0.1); border: 1px solid rgba(34, 211, 238, 0.2); padding: 4px 12px; border-radius: 20px; color: #22d3ee; font-size: 0.7rem; font-weight: bold; }}
    .title {{ font-size: 3rem; font-weight: 800; background: linear-gradient(135deg, #60a5fa, #22d3ee, #10b981); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }}
    
    .status-bar {{ background: rgba(255,255,255,0.03); border: 1px solid rgba(255,255,255,0.1); border-radius: 12px; padding: 10px 20px; display: flex; justify-content: center; gap: 30px; margin-bottom: 2rem; font-size: 0.8rem; }}
    .status-item span {{ color: #6b7fa8; margin-right: 5px; }}
    .status-item b {{ color: #22d3ee; }}
    
    .card {{ background: rgba(10, 14, 28, 0.9); border: 1px solid rgba(60, 130, 255, 0.2); border-radius: 20px; padding: 20px; min-height: 500px; }}
    .card-title {{ font-weight: bold; display: flex; align-items: center; gap: 8px; margin-bottom: 15px; font-size: 0.9rem; }}
    
    .stTextArea textarea {{ background: #080c18 !important; color: #d4dff7 !important; border: 1px solid rgba(255,255,255,0.1) !important; font-family: 'JetBrains Mono', monospace !important; border-radius: 12px !important; }}
    
    .btn-audit {{ background: linear-gradient(135deg, #3b82f6, #22d3ee) !important; border: none !important; border-radius: 12px !important; padding: 12px !important; font-weight: 800 !important; color: white !important; cursor: pointer; }}
    
    .risk-card {{ background: rgba(0,0,0,0.3); border-radius: 15px; padding: 20px; text-align: center; border: 1px solid rgba(255,255,255,0.05); }}
</style>

<div class="header-center">
    <span class="badge">● TEE Verification Active</span>
    <div class="title">Security Auditor</div>
    <div style="color:#6b7fa8; font-size:0.9rem;">AI-powered auditor on OpenGradient TEE</div>
</div>

<div class="status-bar">
    <div class="status-item"><span>Model:</span><b>GEMINI_2_0_FLASH</b></div>
    <div class="status-item"><span>Wallet:</span><b>{acct.address[:6]}...{acct.address[-4:]}</b></div>
    <div class="status-item"><span>Balance:</span><b>{balance} OPG</b></div>
</div>
""", unsafe_allow_html=True)

col1, col2 = st.columns(2)

EXAMPLES = {
    "ERC-20 Example": """// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;
import "@openzeppelin/contracts/token/ERC20/ERC20.sol";
import "@openzeppelin/contracts/access/Ownable.sol";

contract MyToken is ERC20, Ownable {
    uint256 public constant MAX_SUPPLY = 1_000_000 * 1e18;
    constructor() ERC20("MyToken", "MTK") Ownable(msg.sender) {
        _mint(msg.sender, 100_000 * 1e18);
    }
}""",
    "Vulnerable Code": """// SPDX-License-Identifier: MIT
pragma solidity ^0.7.0;
contract VulnerableVault {
    mapping(address => uint256) public balances;
    function withdraw(uint256 amount) public {
        require(balances[msg.sender] >= amount);
        (bool ok, ) = msg.sender.call{value: amount}("");
        require(ok);
        balances[msg.sender] -= amount;
    }
}""",
    "Reentrancy": """// Reentrancy contract example..."""
}

with col1:
    st.markdown('<div class="card-title">📝 Source Code</div>', unsafe_allow_html=True)
    
    # Example buttons in a row
    ex_cols = st.columns(len(EXAMPLES))
    for i, (name, val) in enumerate(EXAMPLES.items()):
        if ex_cols[i].button(name):
            st.session_state.code = val

    code_input = st.text_area("sol", height=400, key="ta", label_visibility="collapsed", value=st.session_state.get("code", ""))

    if st.button("🔍 Start Analysis", key="btn_run", use_container_width=True):
        if not code_input:
            st.error("Paste code first")
        else:
            with st.spinner("TEE Analysis in progress..."):
                try:
                    messages = [
                        {"role": "system", "content": "Analyze Solidity. Return JSON ONLY. {summary, risk_score, vulnerabilities:[]}"},
                        {"role": "user", "content": f"Audit this:\n{code_input}"}
                    ]
                    result = client.llm.chat(
                        model=og.TEE_LLM.GEMINI_2_0_FLASH,
                        messages=messages,
                        max_tokens=1000,
                        x402_settlement_mode=og.x402SettlementMode.SETTLE_BATCH
                    )
                    raw = result.chat_output.get("content", "")
                    if "```json" in raw: raw = raw.split("```json")[1].split("```")[0]
                    st.session_state.audit = json.loads(raw)
                    st.session_state.tx = getattr(result, "payment_hash", None)
                except Exception as e:
                    st.error(f"Error: {e}")

with col2:
    st.markdown('<div class="card-title">📊 Analysis Report</div>', unsafe_allow_html=True)
    if "audit" in st.session_state:
        aud = st.session_state.audit
        score = aud.get("risk_score", 0)
        color = "#ef4444" if score > 70 else "#f59e0b" if score > 30 else "#10b981"
        
        st.markdown(f"""
        <div class="risk-card">
            <div style="font-size:0.7rem; color:#6b7fa8;">Risk Level</div>
            <div style="font-size:3rem; font-weight:800; color:{color};">{score}</div>
            <div style="font-size:0.85rem;">{aud.get('summary', '')}</div>
        </div>
        """, unsafe_allow_html=True)
        
        for v in aud.get("vulnerabilities", []):
            with st.expander(f"⚠️ {v.get('title', 'Finding')}"):
                st.write(v.get('description', ''))
                st.info(f"Fix: {v.get('recommendation', '')}")
                
        if st.session_state.get("tx"):
            st.markdown(f'<div style="text-align:center; margin-top:10px;"><a href="https://sepolia.basescan.org/tx/{st.session_state.tx}" target="_blank" style="color:#22d3ee; font-size:0.7rem;">Verified Tx: {st.session_state.tx[:15]}...</a></div>', unsafe_allow_html=True)
    else:
        st.markdown("""
        <div style="text-align:center; padding-top:100px; color:#6b7fa8;">
            <div style="font-size:3rem; opacity:0.2;">🛡️</div>
            Paste Solidity code and click "Start Analysis"<br>to get a comprehensive report.
        </div>
        """, unsafe_allow_html=True)

st.markdown("""
<div style="text-align:center; margin-top:3rem; color:#6b7fa8; font-size:0.7rem;">
    Powered by <b>OpenGradient</b> Trusted Execution Environment (TEE). Each report is on-chain hash-verified.
</div>
""", unsafe_allow_html=True)
