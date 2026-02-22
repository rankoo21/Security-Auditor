import streamlit as st
import opengradient as og
import os
import json
from web3 import Web3

# 1. Page Config (Must be first)
st.set_page_config(page_title="AI Security Auditor", page_icon="🛡️", layout="wide")

# 2. Get Secrets Safely
pk = st.secrets.get("OG_PRIVATE_KEY") or os.environ.get("OG_PRIVATE_KEY")

# 3. Initialization Logic (Stable & Cached)
@st.cache_resource
def init_client(_pk):
    if not _pk: return None
    try: return og.Client(private_key=_pk)
    except: return None

client = init_client(pk)

# Getting Wallet Info
wallet_addr = "0x000...000"
balance = "0.00"
if pk:
    try:
        w3 = Web3(Web3.HTTPProvider("https://sepolia.base.org"))
        acct = w3.eth.account.from_key(pk)
        wallet_addr = acct.address
        # Simplified balance check
        OPG_TOKEN = "0x240b09731D96979f50B2C649C9CE10FcF9C7987F"
        ABI = [{"inputs":[{"name":"account","type":"address"}],"name":"balanceOf","outputs":[{"name":"","type":"uint256"}],"stateMutability":"view","type":"function"}]
        token = w3.eth.contract(address=OPG_TOKEN, abi=ABI)
        balance = round(token.functions.balanceOf(wallet_addr).call() / 1e18, 3)
    except: pass

# 4. EXAMPLES DATA
EXAMPLES = {
    "ERC-20 Example": "// SPDX-License-Identifier: MIT\npragma solidity ^0.8.20;\nimport \"@openzeppelin/contracts/token/ERC20/ERC20.sol\";\n\ncontract MyToken is ERC20 {\n    constructor() ERC20(\"RankoToken\", \"RNK\") {\n        _mint(msg.sender, 1000000 * 10**18);\n    }\n}",
    "Vulnerable Code": "// SPDX-License-Identifier: MIT\npragma solidity ^0.7.0;\n\ncontract Vulnerable {\n    mapping(address => uint256) public balances;\n    function withdraw(uint256 amount) public {\n        require(balances[msg.sender] >= amount);\n        (bool ok, ) = msg.sender.call{value: amount}(\"\");\n        require(ok);\n        balances[msg.sender] -= amount;\n    }\n}",
    "Reentrancy": "// SPDX-License-Identifier: MIT\npragma solidity ^0.8.0;\n\ncontract Bank {\n    mapping(address => uint) public balances;\n    function withdraw() public {\n        uint bal = balances[msg.sender];\n        require(bal > 0);\n        (bool sent,) = msg.sender.call{value: bal}(\"\");\n        require(sent);\n        balances[msg.sender] = 0;\n    }\n}"
}

# 5. CSS Injection (The glue that makes it look like the original)
st.markdown(f"""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;800&family=JetBrains+Mono&display=swap');

    .stApp {{ background: #04060d; color: #d4dff7; font-family: 'Outfit', sans-serif; }}
    [data-testid="stHeader"] {{ visibility: hidden; }}
    [data-testid="stVerticalBlock"] {{ gap: 0rem; }}
    
    .header-box {{ text-align: center; padding-top: 2rem; margin-bottom: 2rem; }}
    .title-gradient {{
        font-size: 3.5rem; font-weight: 800; line-height: 1.2;
        background: linear-gradient(135deg, #60a5fa 0%, #22d3ee 50%, #10b981 100%);
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;
        filter: drop-shadow(0 0 15px rgba(59, 130, 246, 0.3));
    }}
    .status-bar {{
        display: flex; justify-content: center; gap: 30px; 
        background: rgba(255,255,255,0.03); border: 1px solid rgba(255,255,255,0.08);
        border-radius: 12px; padding: 12px 25px; margin: 1rem auto 3rem; max-width: 850px;
        font-size: 0.78rem; color: #6b7fa8; backdrop-filter: blur(10px);
    }}
    .status-bar b {{ color: #22d3ee; margin-left: 5px; font-family: 'JetBrains Mono'; }}

    /* Panel Styling */
    .panel {{
        background: rgba(10, 14, 28, 0.95);
        border: 1px solid rgba(60, 130, 255, 0.15);
        border-radius: 20px; padding: 25px; min-height: 550px;
    }}
    .panel-title {{ font-weight: 700; font-size: 1rem; margin-bottom: 20px; display: flex; align-items: center; gap: 10px; }}

    /* Inputs & Buttons */
    div[data-baseweb="textarea"] {{ background: #080c18 !important; border: 1px solid rgba(255,255,255,0.05) !important; border-radius: 12px !important; }}
    textarea {{ color: #d4dff7 !important; font-family: 'JetBrains Mono' !important; font-weight: 400 !important; font-size: 0.85rem !important; }}
    
    button[kind="secondary"] {{
        background: rgba(255,255,255,0.05) !important; color: #6b7fa8 !important; 
        border: 1px solid rgba(255,255,255,0.1) !important; border-radius: 99px !important; 
        padding: 5px 20px !important; font-size: 0.75rem !important;
    }}
    button[kind="secondary"]:hover {{ color: #22d3ee !important; border-color: #22d3ee !important; background: rgba(34,211,238,0.05) !important; }}

    .btn-audit button {{
        background: linear-gradient(135deg, #3b82f6, #22d3ee) !important;
        color: white !important; border: none !important; width: 100% !important;
        height: 3.5rem !important; font-size: 1.1rem !important; font-weight: 800 !important;
        box-shadow: 0 4px 20px rgba(59, 130, 246, 0.4) !important; margin-top: 20px !important;
    }}
</style>

<div class="header-box">
    <div class="title-gradient">Security Auditor</div>
    <div style="color:#6b7fa8; margin-top:5px;">TEE-Verified AI Smart Contract Audit</div>
</div>

<div class="status-bar">
    <div>Model: <b>GEMINI_2_0_FLASH</b></div>
    <div>Wallet: <b>{wallet_addr[:6]}...{wallet_addr[-4:]}</b></div>
    <div>Balance: <b>{balance} OPG</b></div>
    <div>Network: <b>Base Sepolia</b></div>
</div>
""", unsafe_allow_html=True)

# 6. APP LAYOUT
col1, col2 = st.columns(2, gap="large")

with col1:
    st.markdown('<div class="panel"><div class="panel-title">📝 Source Code</div>', unsafe_allow_html=True)
    
    # Example Row
    ex_row = st.columns(3)
    if ex_row[0].button("ERC-20 Example", key="ex1"): 
        st.session_state.editor = EXAMPLES["ERC-20 Example"]
        st.rerun()
    if ex_row[1].button("Vulnerable Code", key="ex2"): 
        st.session_state.editor = EXAMPLES["Vulnerable Code"]
        st.rerun()
    if ex_row[2].button("Reentrancy", key="ex3"): 
        st.session_state.editor = EXAMPLES["Reentrancy"]
        st.rerun()

    # Editor
    code_input = st.text_area("in", height=420, key="editor", label_visibility="collapsed")
    
    # Audit Button
    st.markdown('<div class="btn-audit">', unsafe_allow_html=True)
    if st.button("🔍 Start Security Audit", key="run"):
        if not client:
            st.error("❌ SDK Client not initialized. Check your OG_PRIVATE_KEY in Secrets.")
        elif not code_input:
            st.warning("⚠️ Paste code first.")
        else:
            with st.spinner("Analyzing on TEE..."):
                try:
                    sys_p = "Analyze Solidity for vulnerabilities. Return ONLY raw JSON. Schema: {summary: string, risk_score: number, vulnerabilities: [{title, severity, description, recommendation}]}"
                    resp = client.llm.chat(
                        model=og.TEE_LLM.GEMINI_2_0_FLASH,
                        messages=[{"role":"system","content":sys_p}, {"role":"user","content":f"Audit this code:\n{code_input}"}],
                        max_tokens=1500,
                        x402_settlement_mode=og.x402SettlementMode.SETTLE_BATCH
                    )
                    content = resp.chat_output.get("content", "")
                    if "```json" in content: content = content.split("```json")[1].split("```")[0]
                    elif "```" in content: content = content.split("```")[1].split("```")[0]
                    
                    st.session_state.audit_data = json.loads(content)
                    st.session_state.audit_tx = getattr(resp, "payment_hash", None)
                    st.rerun()
                except Exception as e:
                    st.error(f"Audit Error: {e}")
    st.markdown('</div></div>', unsafe_allow_html=True)

with col2:
    st.markdown('<div class="panel"><div class="panel-title">📊 Audit Report</div>', unsafe_allow_html=True)
    
    if "audit_data" in st.session_state:
        data = st.session_state.audit_data
        score = int(data.get("risk_score", 0))
        clr = "#ef4444" if score > 70 else "#f97316" if score > 40 else "#10b981"
        
        st.markdown(f"""
        <div style="background:rgba(0,0,0,0.2); border-radius:15px; padding:30px; text-align:center; border:1px solid rgba(255,255,255,0.05); margin-bottom:1.5rem;">
            <div style="font-size:0.8rem; color:#6b7fa8; text-transform:uppercase; letter-spacing:1px;">Security Risk Score</div>
            <div style="font-size:4.5rem; font-weight:800; color:{clr}; line-height:1; margin:10px 0;">{score}</div>
            <div style="font-size:0.95rem; opacity:0.9;">{data.get('summary','')}</div>
        </div>
        """, unsafe_allow_html=True)
        
        for v in data.get("vulnerabilities", []):
            with st.expander(f"⚠️ {v.get('title','Issue Found')}"):
                st.write(v.get("description",""))
                st.info(f"💡 {v.get('recommendation','')}")
        
        if st.session_state.get("audit_tx"):
            st.markdown(f"""
            <div style="text-align:center; margin-top:2rem;">
                <a href="https://sepolia.basescan.org/tx/{st.session_state.audit_tx}" target="_blank" style="color:#22d3ee; text-decoration:none; border:1px solid rgba(34,211,238,0.3); padding:10px 20px; border-radius:12px; font-size:0.85rem; background:rgba(34,211,238,0.05);">🔗 View On-Chain Proof ↗</a>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div style="text-align:center; padding-top:150px; opacity:0.3;">
            <div style="font-size:5rem;">🛡️</div>
            <div style="font-size:1.2rem; font-weight:600; margin-top:15px;">System Ready</div>
            <div>Paste source code to begin TEE analysis</div>
        </div>
        """, unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

st.markdown("""
<div style="text-align:center; margin-top:5rem; color:#6b7fa8; font-size:0.75rem; opacity:0.6;">
    Protected by OpenGradient TEE • Decentralized Intelligence • © 2026 Security Auditor
</div>
""", unsafe_allow_html=True)
