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

# ─── UNIVERSAL CSS OVERRIDE ───
st.markdown(f"""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;800&family=JetBrains+Mono&display=swap');

    .stApp {{
        background: #04060d;
        color: #d4dff7;
        font-family: 'Outfit', sans-serif;
    }}
    
    [data-testid="stHeader"] {{ background: transparent; }}
    
    .main-title {{
        text-align: center; font-size: 3rem; font-weight: 800; margin-top: 1rem;
        background: linear-gradient(135deg, #60a5fa 0%, #22d3ee 50%, #10b981 100%);
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;
    }}
    .status-bar {{
        display: flex; justify-content: center; gap: 20px; 
        background: rgba(255,255,255,0.03); border: 1px solid rgba(255,255,255,0.1);
        border-radius: 10px; padding: 8px; margin: 1rem auto 2rem; max-width: 800px;
        font-size: 0.75rem; color: #6b7fa8;
    }}
    .status-bar b {{ color: #22d3ee; margin-left: 5px; font-family: 'JetBrains Mono'; }}

    /* Panels */
    .panel-box {{
        background: rgba(10, 14, 28, 0.9);
        border: 1px solid rgba(60, 130, 255, 0.2);
        border-radius: 15px;
        padding: 20px;
        height: 100%;
    }}
    
    .panel-header {{ font-weight: 700; font-size: 0.9rem; margin-bottom: 15px; display: flex; align-items: center; gap: 8px; }}
    
    /* Code Area */
    div[data-baseweb="textarea"] {{ background: #080c18 !important; border: 1px solid rgba(255,255,255,0.05) !important; border-radius: 10px !important; }}
    textarea {{ color: #d4dff7 !important; font-family: 'JetBrains Mono' !important; font-size: 0.82rem !important; }}
    
    /* Buttons */
    .stButton>button {{
        border-radius: 10px !important;
        font-weight: 600 !important;
    }}
    
    .btn-audit-main button {{
        background: linear-gradient(135deg, #3b82f6, #22d3ee) !important;
        color: white !important; border: none !important; width: 100% !important;
        height: 3rem !important; font-size: 1rem !important; margin-top: 15px !important;
    }}
</style>

<div class="main-title">Security Auditor</div>
<div style="text-align:center; color:#6b7fa8; font-size:0.9rem; margin-top:-10px;">AI-powered auditor on OpenGradient TEE</div>

<div class="status-bar">
    <div>Model: <b>GEMINI_2_0_FLASH</b></div>
    <div>Wallet: <b>{wallet_addr[:6]}...{wallet_addr[-4:]}</b></div>
    <div>Balance: <b>{balance} OPG</b></div>
</div>
""", unsafe_allow_html=True)

# ─── LOGIC & DATA ───
EXAMPLES = {{
    "ERC-20 Example": """// SPDX-License-Identifier: MIT\npragma solidity ^0.8.0;\nimport "@openzeppelin/contracts/token/ERC20/ERC20.sol";\n\ncontract MyToken is ERC20 {\n    constructor() ERC20("RankoToken", "RNK") {\n        _mint(msg.sender, 1000 * 10**18);\n    }\n}""",
    "Vulnerable Code": """// SPDX-License-Identifier: MIT\npragma solidity ^0.7.0;\n\ncontract Vulnerable {\n    mapping(address => uint256) public balances;\n    function withdraw(uint256 amount) public {\n        require(balances[msg.sender] >= amount);\n        (bool ok, ) = msg.sender.call{value: amount}("");\n        require(ok);\n        balances[msg.sender] -= amount;\n    }\n}""",
    "Reentrancy": """// Reentrancy contract\npragma solidity ^0.8.0;\ncontract Bank {\n    mapping(address => uint) public balances;\n    function withdraw() public {\n        uint bal = balances[msg.sender];\n        require(bal > 0);\n        (bool sent,) = msg.sender.call{value: bal}("");\n        require(sent);\n        balances[msg.sender] = 0;\n    }\n}"""
}}

col1, col2 = st.columns(2)

with col1:
    st.markdown('<div class="panel-box">', unsafe_allow_html=True)
    st.markdown('<div class="panel-header">📝 Source Code</div>', unsafe_allow_html=True)
    
    # Example buttons
    cols_ex = st.columns(3)
    for i, (name, val) in enumerate(EXAMPLES.items()):
        if cols_ex[i].button(name, key=f"ex_{i}"):
            st.session_state.code = val

    code = st.text_area("code", height=400, key="editor", value=st.session_state.get("code", ""), label_visibility="collapsed")
    st.session_state.code = code

    st.markdown('<div class="btn-audit-main">', unsafe_allow_html=True)
    if st.button("🔍 Start Security Analysis", key="run"):
        if not code:
            st.warning("Please paste code first")
        else:
            with st.spinner("TEE Analysis in progress..."):
                try:
                    prompt = "Analyze Solidity for vulnerabilities. Return ONLY raw JSON. Format: {summary, risk_score, vulnerabilities:[{title, severity, description, recommendation}]}"
                    res = client.llm.chat(
                        model=og.TEE_LLM.GEMINI_2_0_FLASH,
                        messages=[{"role":"system","content":prompt}, {"role":"user","content":f"Audit this:\n{code}"}],
                        max_tokens=1000,
                        x402_settlement_mode=og.x402SettlementMode.SETTLE_BATCH
                    )
                    raw = res.chat_output.get("content", "")
                    if "```json" in raw: raw = raw.split("```json")[1].split("```")[0]
                    elif "```" in raw: raw = raw.split("```")[1].split("```")[0]
                    
                    st.session_state.audit = json.loads(raw)
                    st.session_state.tx = getattr(res, "payment_hash", None)
                    st.rerun()
                except Exception as e:
                    st.error(f"Error: {e}")
    st.markdown('</div></div>', unsafe_allow_html=True)

with col2:
    st.markdown('<div class="panel-box">', unsafe_allow_html=True)
    st.markdown('<div class="panel-header">📊 Analysis Report</div>', unsafe_allow_html=True)
    
    if "audit" in st.session_state:
        aud = st.session_state.audit
        # CRITICAL FIX: Ensure score is int and not None
        try:
            raw_score = aud.get("risk_score", 0)
            score = int(raw_score) if raw_score is not None else 0
        except:
            score = 0
            
        color = "#ef4444" if score > 70 else "#f97316" if score > 40 else "#10b981"
        
        st.markdown(f"""
        <div style="text-align:center; padding:20px; background:rgba(0,0,0,0.2); border-radius:12px; margin-bottom:1rem;">
            <div style="font-size:0.7rem; color:#6b7fa8;">Risk Level Score</div>
            <div style="font-size:3.5rem; font-weight:800; color:{color}; line-height:1;">{score}</div>
            <div style="font-size:0.85rem; margin-top:10px;">{aud.get('summary','')}</div>
        </div>
        """, unsafe_allow_html=True)
        
        for v in aud.get('vulnerabilities', []):
            with st.expander(f"⚠️ {v.get('title','Finding')}"):
                st.write(v.get('description',''))
                st.info(f"💡 {v.get('recommendation','')}")
                
        if st.session_state.get("tx"):
            st.markdown(f'<div style="text-align:center; margin-top:15px;"><a href="https://sepolia.basescan.org/tx/{st.session_state.tx}" target="_blank" style="color:#22d3ee; font-size:0.7rem;">Verified Tx: {st.session_state.tx[:15]}...</a></div>', unsafe_allow_html=True)
    else:
        st.markdown("""
        <div style="text-align:center; padding-top:100px; color:#6b7fa8; opacity:0.5;">
            <div style="font-size:3rem; margin-bottom:15px;">🛡️</div>
            Paste code and click Start Analysis to begin.
        </div>
        """, unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)
