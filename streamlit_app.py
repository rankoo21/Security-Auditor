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

# ─── PREMIUM CSS OVERRIDE ───
st.markdown(f"""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;800&family=JetBrains+Mono&display=swap');

    .stApp {{ background: #04060d; color: #d4dff7; font-family: 'Outfit', sans-serif; }}
    [data-testid="stHeader"] {{ background: transparent; visibility: hidden; }}
    
    .main-title {{
        text-align: center; font-size: 3.5rem; font-weight: 800; margin-top: 1rem;
        background: linear-gradient(135deg, #60a5fa 0%, #22d3ee 50%, #10b981 100%);
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;
        filter: drop-shadow(0 4px 20px rgba(59, 130, 246, 0.4));
    }}
    .status-bar {{
        display: flex; justify-content: center; gap: 40px; 
        background: rgba(255,255,255,0.03); border: 1px solid rgba(255,255,255,0.1);
        border-radius: 14px; padding: 12px 25px; margin: 1.5rem auto 3rem; max-width: 900px;
        font-size: 0.8rem; color: #6b7fa8; backdrop-filter: blur(12px);
    }}
    .status-bar b {{ color: #22d3ee; margin-left: 5px; font-family: 'JetBrains Mono'; }}

    /* Panels UI */
    .panel {{
        background: rgba(10, 14, 28, 0.9);
        border: 1px solid rgba(60, 130, 255, 0.2);
        border-radius: 20px; padding: 30px; height: 100%;
        box-shadow: 0 15px 50px rgba(0,0,0,0.5);
    }}
    .panel-title {{ font-weight: 800; font-size: 1.1rem; margin-bottom: 25px; display: flex; align-items: center; gap: 12px; color: #fff; }}

    /* Editor Styling */
    div[data-baseweb="textarea"] {{ background: #080c18 !important; border: 1px solid rgba(255,255,255,0.1) !important; border-radius: 12px !important; }}
    textarea {{ color: #d4dff7 !important; font-family: 'JetBrains Mono' !important; font-size: 0.9rem !important; line-height: 1.6 !important; }}
    
    /* Buttons UI */
    .stButton>button {{
        border-radius: 12px !important;
        transition: all 0.3s ease !important;
        font-family: 'Outfit', sans-serif !important;
    }}
    
    /* Small Pills */
    button[kind="secondary"] {{
        background: rgba(255,255,255,0.05) !important; color: #6b7fa8 !important; 
        border: 1px solid rgba(255,255,255,0.1) !important; font-size: 0.75rem !important;
        border-radius: 99px !important; padding: 6px 18px !important; margin-bottom: 10px !important;
    }}
    button[kind="secondary"]:hover {{ background: rgba(34, 211, 238, 0.1) !important; color: #22d3ee !important; border-color: #22d3ee !important; transform: scale(1.05); }}

    /* Audit Button */
    .btn-audit-main button {{
        background: linear-gradient(135deg, #3b82f6, #22d3ee) !important;
        color: white !important; border: none !important; width: 100% !important;
        height: 3.8rem !important; font-size: 1.2rem !important; font-weight: 800 !important;
        box-shadow: 0 6px 25px rgba(59, 130, 246, 0.4) !important; margin-top: 25px !important;
        text-transform: uppercase; letter-spacing: 1px;
    }}
    .btn-audit-main button:hover {{ transform: translateY(-3px); box-shadow: 0 10px 35px rgba(59, 130, 246, 0.6) !important; }}
</style>

<div class="main-title">Security Auditor</div>
<div style="text-align:center; color:#6b7fa8; font-size:1.1rem; margin-top:-12px; margin-bottom:1rem;">🛡️ AI-powered auditor on OpenGradient TEE</div>

<div class="status-bar">
    <div>Model: <b>GEMINI_2_0_FLASH</b></div>
    <div>Wallet: <b>{wallet_addr[:6]}...{wallet_addr[-4:]}</b></div>
    <div>Balance: <b>{balance} OPG</b></div>
    <div>Network: <b>Base Sepolia</b></div>
</div>
""", unsafe_allow_html=True)

# ─── DATA & EXAMPLES ───
EXAMPLES = {
    "ERC-20 Example": "// SPDX-License-Identifier: MIT\npragma solidity ^0.8.20;\nimport \"@openzeppelin/contracts/token/ERC20/ERC20.sol\";\n\ncontract MyToken is ERC20 {\n    constructor() ERC20(\"RankoToken\", \"RNK\") {\n        _mint(msg.sender, 1000000 * 10**18);\n    }\n}",
    "Vulnerable Code": "// SPDX-License-Identifier: MIT\npragma solidity ^0.7.0;\n\ncontract Vulnerable {\n    mapping(address => uint256) public balances;\n    function withdraw(uint256 amount) public {\n        require(balances[msg.sender] >= amount);\n        (bool ok, ) = msg.sender.call{value: amount}(\"\");\n        require(ok);\n        balances[msg.sender] -= amount;\n    }\n}",
    "Reentrancy": "// SPDX-License-Identifier: MIT\npragma solidity ^0.8.0;\n\ncontract Bank {\n    mapping(address => uint) public balances;\n    function withdraw() public {\n        uint bal = balances[msg.sender];\n        require(bal > 0);\n        (bool sent,) = msg.sender.call{value: bal}(\"\");\n        require(sent);\n        balances[msg.sender] = 0;\n    }\n}"
}

# ─── MAIN APP GRID ───
col1, col2 = st.columns(2, gap="large")

with col1:
    st.markdown('<div class="panel">', unsafe_allow_html=True)
    st.markdown('<div class="panel-title">📝 Source Code</div>', unsafe_allow_html=True)
    
    # Example buttons loading logic
    cols_ex = st.columns(3)
    if cols_ex[0].button("ERC-20 Example", key="ex1"): 
        st.session_state.editor = EXAMPLES["ERC-20 Example"]
        st.rerun()
    if cols_ex[1].button("Vulnerable Code", key="ex2"): 
        st.session_state.editor = EXAMPLES["Vulnerable Code"]
        st.rerun()
    if cols_ex[2].button("Reentrancy Example", key="ex3"): 
        st.session_state.editor = EXAMPLES["Reentrancy"]
        st.rerun()

    # The editor itself (bound to st.session_state.editor)
    input_code = st.text_area("c", height=450, key="editor", label_visibility="collapsed")
    
    st.markdown('<div class="btn-audit-main">', unsafe_allow_html=True)
    if st.button("🔍 Start Security Analysis", key="run_btn"):
        if not input_code:
            st.warning("Please paste code first")
        else:
            with st.spinner("TEE Analysis in progress..."):
                try:
                    p = "Analyze Solidity for vulnerabilities. Return ONLY raw JSON. Format: {summary, risk_score, vulnerabilities:[{title, severity, description, recommendation}]}"
                    m = [{"role":"system","content":p}, {"role":"user","content":f"Audit this:\n{input_code}"}]
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
        <div style="background:rgba(0,0,0,0.3); border-radius:18px; padding:35px; text-align:center; border:1px solid rgba(255,255,255,0.05); margin-bottom:2rem;">
            <div style="font-size:0.85rem; color:#6b7fa8; margin-bottom:12px; text-transform:uppercase; letter-spacing:1.5px;">Security Risk Score</div>
            <div style="font-size:4.5rem; font-weight:800; color:{s_color}; line-height:1;">{s_val}</div>
            <div style="font-size:1.05rem; margin-top:25px; line-height:1.7;">{aud.get('summary','')}</div>
        </div>
        """, unsafe_allow_html=True)
        
        # Findings list
        for v in aud.get('vulnerabilities', []):
            sev = v.get('severity', 'Low').upper()
            scol = "#ef4444" if sev == "CRITICAL" else "#f97316" if sev == "HIGH" else "#f59e0b"
            with st.expander(f"⚠️ {v.get('title','Finding')}"):
                st.markdown(f"<span style='color:{scol}; font-weight:bold; font-size:0.75rem;'>SEVERITY: {sev}</span>", unsafe_allow_html=True)
                st.markdown(f"<p style='font-size:0.92rem; margin-top:10px;'>{v.get('description','')}</p>", unsafe_allow_html=True)
                st.markdown(f"<div style='background:rgba(34,211,238,0.06); padding:15px; border-radius:12px; border-left:4px solid #22d3ee; font-size:0.9rem; margin-top:12px;'><b>💡 Recommendation:</b><br>{v.get('recommendation','')}</div>", unsafe_allow_html=True)
                
        if st.session_state.get("tx_h"):
            st.markdown(f'<div style="text-align:center; margin-top:25px;"><a href="https://sepolia.basescan.org/tx/{st.session_state.tx_h}" target="_blank" style="color:#22d3ee; font-size:0.85rem; text-decoration:none; padding:12px 25px; border:1px solid rgba(34,211,238,0.3); border-radius:12px; background:rgba(34,211,238,0.05);">🔗 View On-Chain Proof ↗</a></div>', unsafe_allow_html=True)
    else:
        st.markdown("""
        <div style="text-align:center; padding-top:150px; color:#6b7fa8; opacity:0.3;">
            <div style="font-size:5rem; margin-bottom:25px;">🛡️</div>
            <div style="font-weight:800; font-size:1.2rem; letter-spacing:1px;">Ready for Analysis</div>
            <div style="font-size:0.85rem; margin-top:12px;">Paste code to generate persistent report</div>
        </div>
        """, unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

st.markdown("""
<div style="text-align:center; margin-top:6rem; color:#6b7fa8; font-size:0.75rem; border-top:1px solid rgba(255,255,255,0.05); padding-top:30px; opacity:0.8;">
    © 2026 AI Security Auditor • Powered by <b>OpenGradient TEE</b> Infrastructure • Base Sepolia Network
</div>
""", unsafe_allow_html=True)
