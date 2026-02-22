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

# Initialize SDK and get balance
balance = "0.00"
wallet_addr = "0x000...000"

if pk:
    try:
        w3 = Web3(Web3.HTTPProvider("https://sepolia.base.org"))
        acct = w3.eth.account.from_key(pk)
        wallet_addr = acct.address
        client = og.Client(private_key=pk)
        
        # OPG Balance check
        def get_opg_balance():
            try:
                OPG_TOKEN = "0x240b09731D96979f50B2C649C9CE10FcF9C7987F"
                ERC20_ABI = [{"inputs":[{"name":"account","type":"address"}],"name":"balanceOf","outputs":[{"name":"","type":"uint256"}],"stateMutability":"view","type":"function"}]
                token = w3.eth.contract(address=OPG_TOKEN, abi=ERC20_ABI)
                raw = token.functions.balanceOf(wallet_addr).call()
                return round(raw / 1e18, 3)
            except: return "0.00"
        
        balance = get_opg_balance()
    except: pass
else:
    st.error("🔑 Private Key missing in Secrets!")
    st.stop()

# ─── THE CORE DESIGN SYSTEM (CSS INJECTION) ───
st.markdown(f"""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;700;800&family=JetBrains+Mono&display=swap');

    :root {{
        --void: #04060d;
        --deep: #080c18;
        --card: rgba(10, 14, 28, 0.9);
        --glass: rgba(40, 120, 255, 0.06);
        --border: rgba(60, 130, 255, 0.2);
        --blue1: #3b82f6;
        --blue2: #60a5fa;
        --cyan: #22d3ee;
        --green: #10b981;
        --text: #d4dff7;
        --muted: #6b7fa8;
    }}

    .stApp {{
        background: var(--void);
        color: var(--text);
        font-family: 'Outfit', sans-serif;
    }}

    /* Hide Streamlit elements */
    [data-testid="stHeader"], [data-testid="stFooter"] {{ visibility: hidden; }}
    
    /* Background Globs */
    .stApp::before {{
        content: ''; position: fixed; width: 600px; height: 600px; border-radius: 50%;
        filter: blur(100px); background: radial-gradient(circle, rgba(59, 130, 246, 0.08) 0%, transparent 70%);
        top: -200px; right: -100px; pointer-events: none; z-index: -1;
    }}
    
    .header-container {{ text-align: center; margin-bottom: 2rem; padding-top: 2rem; }}
    .badge {{ 
        display: inline-flex; align-items: center; gap: 8px; background: var(--glass);
        border: 1px solid var(--border); border-radius: 99px; padding: 5px 15px;
        font-size: 0.72rem; font-weight: 700; color: var(--cyan); margin-bottom: 1rem;
    }}
    .dot {{ width: 6px; height: 6px; background: var(--green); border-radius: 50%; box-shadow: 0 0 8px var(--green); }}
    
    .main-title {{
        font-size: 3.2rem; font-weight: 800; line-height: 1.2;
        background: linear-gradient(135deg, #60a5fa 0%, #22d3ee 50%, #10b981 100%);
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;
        filter: drop-shadow(0 0 20px rgba(59, 130, 246, 0.25));
    }}
    .subtitle {{ color: var(--muted); font-size: 1rem; margin-top: 5px; }}
    
    .status-bar {{
        display: flex; justify-content: center; gap: 2rem; background: var(--glass);
        border: 1px solid var(--border); border-radius: 12px; padding: 10px 20px;
        font-size: 0.75rem; color: var(--muted); margin-bottom: 2rem;
    }}
    .status-bar st {{ color: var(--cyan); font-weight: 600; font-family: 'JetBrains Mono'; margin-left: 5px; }}

    .panel {{
        background: var(--card); border: 1px solid var(--border); border-radius: 20px;
        padding: 0; overflow: hidden; height: auto; display: flex; flex-direction: column;
    }}
    .panel-header {{
        padding: 12px 20px; border-bottom: 1px solid rgba(255,255,255,0.05);
        font-size: 0.85rem; font-weight: 700; display: flex; align-items: center; gap: 10px;
    }}
    
    /* Override Streamlit Inputs */
    div[data-baseweb="textarea"] {{ background: rgba(0,0,0,0.3) !important; border-radius: 12px !important; border: 1px solid rgba(255,255,255,0.06) !important; }}
    textarea {{ background: transparent !important; color: var(--text) !important; font-family: 'JetBrains Mono' !important; font-size: 0.82rem !important; }}
    
    button[kind="secondary"] {{
        background: rgba(255,255,255,0.05) !important; color: var(--muted) !important; 
        border: 1px solid var(--border) !important; font-size: 0.72rem !important;
        border-radius: 8px !important; padding: 5px 12px !important; opacity: 0.8;
    }}
    button[kind="secondary"]:hover {{ opacity: 1; color: var(--text) !important; border-color: var(--blue2) !important; }}

    .btn-audit-wrap div button {{
        background: linear-gradient(135deg, var(--blue1), var(--cyan)) !important;
        color: white !important; font-weight: 700 !important; border: none !important;
        border-radius: 12px !important; padding: 12px !important; width: 100% !important;
        box-shadow: 0 4px 20px rgba(59, 130, 246, 0.35) !important; font-size: 0.95rem !important;
    }}
</style>

<div class="header-container">
    <div class="badge"><div class="dot"></div> TEE Verification Active</div>
    <div class="main-title">Security Auditor</div>
    <div class="subtitle">AI-powered auditor on OpenGradient TEE</div>
</div>

<div class="status-bar">
    <div>Model: <st>GEMINI_2_0_FLASH</st></div>
    <div>Wallet: <st>{wallet_addr[:6]}...{wallet_addr[-4:]}</st></div>
    <div>Balance: <st>{balance} OPG</st></div>
    <div>Network: <st>Base Sepolia</st></div>
</div>
""", unsafe_allow_html=True)

# ─── DATA & EXAMPLES ───
EXAMPLES = {
    "erc20": """// SPDX-License-Identifier: MIT\npragma solidity ^0.8.20;\nimport "@openzeppelin/contracts/token/ERC20/ERC20.sol";\n\ncontract MyToken is ERC20 {\n    constructor() ERC20("RankoToken", "RNK") {\n        _mint(msg.sender, 1000000 * 10**18);\n    }\n}""",
    "vuln": """// SPDX-License-Identifier: MIT\npragma solidity ^0.7.0;\n\ncontract Vulnerable {\n    mapping(address => uint256) public balances;\n    function withdraw(uint256 amount) public {\n        require(balances[msg.sender] >= amount);\n        (bool ok, ) = msg.sender.call{value: amount}("");\n        require(ok);\n        balances[msg.sender] -= amount;\n    }\n}""",
    "reentrancy": """// Reentrancy Example\npragma solidity ^0.8.0;\n\ncontract Bank {\n    mapping(address => uint) public balances;\n    function withdraw() public {\n        uint bal = balances[msg.sender];\n        require(bal > 0);\n        (bool sent,) = msg.sender.call{value: bal}("");\n        require(sent);\n        balances[msg.sender] = 0;\n    }\n}"""
}

# ─── MAIN APP GRID ───
col1, col2 = st.columns(2, gap="large")

with col1:
    st.markdown('<div class="panel-header">📝 Source Code</div>', unsafe_allow_html=True)
    
    # Example buttons row
    btn_cols = st.columns(3)
    if btn_cols[0].button("ERC-20 Example"): st.session_state.code = EXAMPLES["erc20"]
    if btn_cols[1].button("Vulnerable Code"): st.session_state.code = EXAMPLES["vuln"]
    if btn_cols[2].button("Reentrancy"): st.session_state.code = EXAMPLES["reentrancy"]
    
    code = st.text_area("sol_code", height=400, key="editor", value=st.session_state.get("code", ""), label_visibility="collapsed")
    st.session_state.code = code

    st.markdown('<div class="btn-audit-wrap">', unsafe_allow_html=True)
    if st.button("🔍 Start Analysis", key="run"):
        if not code:
            st.warning("Please paste code first")
        else:
            with st.spinner("TEE Analysis in progress..."):
                try:
                    prompt = "Analyze Solidity for vulnerabilities. Return ONLY raw JSON. Format: {summary, risk_score, vulnerabilities:[{title, severity, description, recommendation}]}"
                    messages = [{"role":"system","content":prompt}, {"role":"user","content":f"Audit this code:\n{code}"}]
                    
                    res = client.llm.chat(
                        model=og.TEE_LLM.GEMINI_2_0_FLASH,
                        messages=messages,
                        max_tokens=1000,
                        x402_settlement_mode=og.x402SettlementMode.SETTLE_BATCH
                    )
                    
                    raw = res.chat_output.get("content", "")
                    if "```json" in raw: raw = raw.split("```json")[1].split("```")[0]
                    elif "```" in raw: raw = raw.split("```")[1].split("```")[0]
                    
                    st.session_state.audit = json.loads(raw)
                    st.session_state.tx_hash = getattr(res, "payment_hash", None)
                    st.rerun()
                except Exception as e:
                    st.error(f"Error: {e}")
    st.markdown('</div>', unsafe_allow_html=True)

with col2:
    st.markdown('<div class="panel-header">📊 Analysis Report</div>', unsafe_allow_html=True)
    
    if "audit" in st.session_state:
        aud = st.session_state.audit
        # Risk section
        score = aud.get("risk_score", 0)
        color = "#ef4444" if score > 70 else "#f97316" if score > 40 else "#10b981"
        
        st.markdown(f"""
        <div style="background:rgba(0,0,0,0.2); border-radius:15px; padding:25px; text-align:center; border:1px solid rgba(255,255,255,0.05); margin-bottom:1rem;">
            <div style="font-size:0.75rem; color:var(--muted); margin-bottom:10px;">Security Risk Score</div>
            <div style="font-size:3.5rem; font-weight:800; color:{color}; line-height:1;">{score}</div>
            <div style="font-size:0.9rem; margin-top:15px; line-height:1.6;">{aud.get('summary','')}</div>
        </div>
        """, unsafe_allow_html=True)
        
        # Findings List
        for i, v in enumerate(aud.get('vulnerabilities', [])):
            sev = v.get('severity', 'Info').lower()
            bor_col = {"critical":"#ef4444", "high":"#f97316", "medium":"#f59e0b", "low":"#60a5fa", "info":"#6b7fa8"}.get(sev, "#6b7fa8")
            
            with st.expander(f"{v.get('title','Finding')}"):
                st.markdown(f"<small style='color:{bor_col}; font-weight:bold;'>SEVERITY: {sev.upper()}</small>", unsafe_allow_html=True)
                st.write(v.get('description',''))
                st.markdown(f"<div style='background:rgba(34,211,238,0.05); padding:10px; border-radius:8px; border-left:2px solid #22d3ee; font-size:0.85rem;'>💡 {v.get('recommendation','')}</div>", unsafe_allow_html=True)

        if st.session_state.get("tx_hash"):
            st.markdown(f"""
            <div style="text-align:center; margin-top:20px;">
                <a href="https://sepolia.basescan.org/tx/{st.session_state.tx_hash}" target="_blank" style="color:var(--cyan); font-size:0.75rem; text-decoration:none; border:1px solid var(--border); padding:5px 12px; border-radius:8px;">View On-Chain Proof ↗</a>
            </div>
            """, unsafe_allow_html=True)
            
    else:
        st.markdown("""
        <div style="opacity:0.25; text-align:center; padding-top:100px;">
            <div style="font-size:4rem; margin-bottom:20px;">🛡️</div>
            <div style="font-size:0.9rem;">Ready for Analysis</div>
            <div style="font-size:0.75rem; margin-top:8px;">Paste code and click Start Analysis to begin.</div>
        </div>
        """, unsafe_allow_html=True)

st.markdown("""
<div style="text-align:center; margin-top:5rem; color:var(--muted); font-size:0.7rem; border-top:1px solid rgba(255,255,255,0.05); padding-top:20px;">
    Verified and persistent security auditing powered by <b>OpenGradient TEE</b> Infrastructure.
</div>
""", unsafe_allow_html=True)
