import streamlit as st
import opengradient as og
import os
import json
import time
from web3 import Web3

# Page setup
st.set_page_config(page_title="Security Auditor", page_icon="🛡️", layout="wide")

# Get PK safely
pk = st.secrets.get("OG_PRIVATE_KEY") or os.environ.get("OG_PRIVATE_KEY")

# Initialization logic
balance = "0.00"
wallet_addr = "0x000...000"

if pk:
    try:
        w3 = Web3(Web3.HTTPProvider("https://sepolia.base.org"))
        acct = w3.eth.account.from_key(pk)
        wallet_addr = acct.address
        client = og.Client(private_key=pk)
        OPG_TOKEN = "0x240b09731D96979f50B2C649C9CE10FcF9C7987F"
        ERC20_ABI = [{"inputs":[{"name":"account","type":"address"}],"name":"balanceOf","outputs":[{"name":"","type":"uint256"}],"stateMutability":"view","type":"function"}]
        token = w3.eth.contract(address=OPG_TOKEN, abi=ERC20_ABI)
        raw = token.functions.balanceOf(wallet_addr).call()
        balance = round(raw / 1e18, 3)
    except: pass
else:
    st.error("🔑 Private Key missing in Secrets!")
    st.stop()

# ─── THE STYLE OVERHAUL ───
st.markdown(f"""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;800&family=JetBrains+Mono&display=swap');

    .stApp {{ background: #04060d; color: #d4dff7; font-family: 'Outfit', sans-serif; }}
    [data-testid="stHeader"] {{ background: transparent; }}
    
    .main-title {{
        text-align: center; font-size: 3.2rem; font-weight: 800; margin-top: 2rem;
        background: linear-gradient(135deg, #60a5fa 0%, #22d3ee 50%, #10b981 100%);
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;
        filter: drop-shadow(0 0 20px rgba(59, 130, 246, 0.3));
    }}
    .status-bar {{
        display: flex; justify-content: center; gap: 30px; 
        background: rgba(255,255,255,0.03); border: 1px solid rgba(255,255,255,0.1);
        border-radius: 12px; padding: 10px 20px; margin: 1.5rem auto 2.5rem; max-width: 900px;
        font-size: 0.75rem; color: #6b7fa8; backdrop-filter: blur(10px);
    }}
    .status-bar b {{ color: #22d3ee; margin-left: 5px; font-family: 'JetBrains Mono'; }}

    .panel {{
        background: rgba(10, 14, 28, 0.9);
        border: 1px solid rgba(60, 130, 255, 0.2);
        border-radius: 20px; padding: 25px; height: 100%;
        box-shadow: 0 10px 40px rgba(0,0,0,0.4);
    }}
    .panel-title {{ font-weight: 700; font-size: 1rem; margin-bottom: 20px; display: flex; align-items: center; gap: 10px; }}

    div[data-baseweb="textarea"] {{ background: #080c18 !important; border: 1px solid rgba(255,255,255,0.1) !important; border-radius: 12px !important; }}
    textarea {{ color: #d4dff7 !important; font-family: 'JetBrains Mono' !important; font-size: 0.85rem !important; }}
    
    .stButton>button {{
        border-radius: 12px !important;
        transition: all 0.2s !important;
    }}
    
    .btn-audit-main button {{
        background: linear-gradient(135deg, #3b82f6, #22d3ee) !important;
        color: white !important; border: none !important; width: 100% !important;
        height: 3.5rem !important; font-size: 1.1rem !important; font-weight: 700 !important;
        box-shadow: 0 4px 20px rgba(59, 130, 246, 0.4) !important; margin-top: 20px !important;
    }}
    .btn-audit-main button:hover {{ transform: translateY(-2px); box-shadow: 0 8px 30px rgba(59, 130, 246, 0.6) !important; }}
</style>

<div class="main-title">Security Auditor</div>
<div style="text-align:center; color:#6b7fa8; font-size:1rem; margin-top:-10px;">🛡️ AI-powered auditor on OpenGradient TEE</div>

<div class="status-bar">
    <div>Model: <b>GEMINI_2_0_FLASH</b></div>
    <div>Wallet: <b>{wallet_addr[:6]}...{wallet_addr[-4:]}</b></div>
    <div>Balance: <b>{balance} OPG</b></div>
    <div>Network: <b>Base Sepolia</b></div>
</div>
""", unsafe_allow_html=True)

# ─── DATA & EXAMPLES (FIXED SYNTAX) ───
EXAMPLES = {
    "ERC-20 Example": "// SPDX-License-Identifier: MIT\\npragma solidity ^0.8.20;\\nimport \\\"@openzeppelin/contracts/token/ERC20/ERC20.sol\\\";\\n\\ncontract MyToken is ERC20 {\\n    constructor() ERC20(\\\"RankoToken\\\", \\\"RNK\\\") {\\n        _mint(msg.sender, 1000000 * 10**18);\\n    }\\n}",
    "Vulnerable Code": "// SPDX-License-Identifier: MIT\\npragma solidity ^0.7.0;\\n\\ncontract Vulnerable {\\n    mapping(address => uint256) public balances;\\n    function withdraw(uint256 amount) public {\\n        require(balances[msg.sender] >= amount);\\n        (bool ok, ) = msg.sender.call{value: amount}(\\\"\\\");\\n        require(ok);\\n        balances[msg.sender] -= amount;\\n    }\\n}",
    "Reentrancy": "// Reentrancy example\\npragma solidity ^0.8.0;\\n\\ncontract Bank {\\n    mapping(address => uint) public balances;\\n    function withdraw() public {\\n        uint bal = balances[msg.sender];\\n        require(bal > 0);\\n        (bool sent,) = msg.sender.call{value: bal}(\\\"\\\");\\n        require(sent);\\n        balances[msg.sender] = 0;\\n    }\\n}"
}

col1, col2 = st.columns(2, gap="large")

with col1:
    st.markdown('<div class="panel">', unsafe_allow_html=True)
    st.markdown('<div class="panel-title">📝 Source Code</div>', unsafe_allow_html=True)
    
    # Example buttons
    cols_ex = st.columns(3)
    if cols_ex[0].button("ERC-20", key="ex1"): st.session_state.code = EXAMPLES["ERC-20 Example"]
    if cols_ex[1].button("Vulnerable", key="ex2"): st.session_state.code = EXAMPLES["Vulnerable Code"]
    if cols_ex[2].button("Reentrancy", key="ex3"): st.session_state.code = EXAMPLES["Reentrancy"]

    input_code = st.text_area("c", height=420, key="editor", value=st.session_state.get("code", ""), label_visibility="collapsed")
    st.session_state.code = input_code

    st.markdown('<div class="btn-audit-main">', unsafe_allow_html=True)
    if st.button("🔍 Start Security Analysis", key="run_btn"):
        if not input_code:
            st.warning("Please paste code first")
        else:
            with st.spinner("TEE Analysis in progress..."):
                try:
                    p = "Analyze Solidity for vulnerabilities. Return ONLY raw JSON. Format: {summary, risk_score, vulnerabilities:[{title, severity, description, recommendation}]}"
                    m = [{"role":"system","content":p}, {"role":"user","content":f"Audit this:\\n{input_code}"}]
                    r = client.llm.chat(model=og.TEE_LLM.GEMINI_2_0_FLASH, messages=m, max_tokens=1000, x402_settlement_mode=og.x402SettlementMode.SETTLE_BATCH)
                    raw_out = r.chat_output.get("content", "")
                    if "```json" in raw_out: raw_out = raw_out.split("```json")[1].split("```")[0]
                    elif "```" in raw_out: raw_out = raw_out.split("```")[1].split("```")[0]
                    st.session_state.audit_res = json.loads(raw_out)
                    st.session_state.tx_h = getattr(r, "payment_hash", None)
                    st.rerun()
                except Exception as ex:
                    st.error(f"Error: {ex}")
    st.markdown('</div></div>', unsafe_allow_html=True)

with col2:
    st.markdown('<div class="panel">', unsafe_allow_html=True)
    st.markdown('<div class="panel-title">📊 Analysis Report</div>', unsafe_allow_html=True)
    
    if "audit_res" in st.session_state:
        aud = st.session_state.audit_res
        try:
            s_val = int(aud.get("risk_score", 0))
        except: s_val = 0
            
        s_color = "#ef4444" if s_val > 70 else "#f97316" if s_val > 40 else "#10b981"
        
        st.markdown(f"""
        <div style="background:rgba(0,0,0,0.3); border-radius:15px; padding:30px; text-align:center; border:1px solid rgba(255,255,255,0.05); margin-bottom:1.5rem;">
            <div style="font-size:0.8rem; color:#6b7fa8; margin-bottom:10px; text-transform:uppercase; letter-spacing:1px;">Risk Score</div>
            <div style="font-size:4rem; font-weight:800; color:{s_color}; line-height:1;">{s_val}</div>
            <div style="font-size:0.95rem; margin-top:20px; line-height:1.6;">{aud.get('summary','')}</div>
        </div>
        """, unsafe_allow_html=True)
        
        for v in aud.get('vulnerabilities', []):
            with st.expander(f"⚠️ {v.get('title','Finding')}"):
                st.markdown(f"<p style='font-size:0.85rem;'>{v.get('description','')}</p>", unsafe_allow_html=True)
                st.markdown(f"<div style='background:rgba(34,211,238,0.05); padding:12px; border-radius:10px; border-left:3px solid #22d3ee; font-size:0.85rem; margin-top:10px;'>💡 <b>Recommendation:</b> {v.get('recommendation','')}</div>", unsafe_allow_html=True)
                
        if st.session_state.get("tx_h"):
            st.markdown(f'<div style="text-align:center; margin-top:20px;"><a href="https://sepolia.basescan.org/tx/{st.session_state.tx_h}" target="_blank" style="color:#22d3ee; font-size:0.8rem; text-decoration:none; padding:10px 20px; border:1px solid rgba(34,211,238,0.2); border-radius:12px;">🔗 View On-Chain Proof</a></div>', unsafe_allow_html=True)
    else:
        st.markdown("""
        <div style="text-align:center; padding-top:120px; color:#6b7fa8; opacity:0.3;">
            <div style="font-size:4.5rem; margin-bottom:20px;">🛡️</div>
            <div style="font-weight:600;">System Ready</div>
            <div style="font-size:0.75rem; margin-top:10px;">Paste code to generate report</div>
        </div>
        """, unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)
