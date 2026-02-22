import streamlit as st
import opengradient as og
import os
import json
import time
from web3 import Web3

# 1. Page Configuration
st.set_page_config(page_title="AI Smart Contract Auditor", page_icon="🛡️", layout="wide")

# 2. Premium Design (Extracted from Localhost index.html)
# Overriding Streamlit's default layout more aggressively
st.markdown(r"""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;700;800&family=JetBrains+Mono:wght@400;500;600&display=swap');

    /* Reset & Base */
    .stApp { background: #04060d; color: #d4dff7; font-family: 'Outfit', sans-serif; }
    [data-testid="stHeader"] { visibility: hidden; }
    [data-testid="stVerticalBlock"] { gap: 0rem; }
    [data-testid="stSidebar"] { background-color: #080c18; }

    /* Animated Background (Pure CSS) */
    .stApp::before {
        content: ''; position: fixed; width: 700px; height: 700px; border-radius: 50%;
        filter: blur(100px); background: radial-gradient(circle, rgba(59, 130, 246, 0.1) 0%, transparent 70%);
        top: -300px; right: -200px; z-index: 0; pointer-events: none;
    }

    /* Core UI Components */
    .title-area { text-align: center; padding: 40px 0 20px; }
    .badge-tee {
        display: inline-flex; align-items: center; gap: 8px;
        background: rgba(40, 120, 255, 0.06); border: 1px solid rgba(60, 130, 255, 0.2);
        border-radius: 99px; padding: 6px 16px; font-size: 0.75rem; 
        font-weight: 700; color: #22d3ee; margin-bottom: 15px; backdrop-filter: blur(10px);
    }
    .badge-tee::before { content: ''; width: 6px; height: 6px; border-radius: 50%; background: #10b981; box-shadow: 0 0 8px #10b981; }
    
    .title-gradient {
        font-size: clamp(2.5rem, 5vw, 4rem); font-weight: 800; line-height: 1.1;
        background: linear-gradient(135deg, #60a5fa 0%, #22d3ee 50%, #10b981 100%);
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;
        filter: drop-shadow(0 0 15px rgba(59, 130, 246, 0.3));
    }
    
    .status-bar-custom {
        display: flex; justify-content: center; gap: 20px; flex-wrap: wrap;
        background: rgba(40, 120, 255, 0.05); border: 1px solid rgba(60, 130, 255, 0.2);
        border-radius: 12px; padding: 10px 20px; margin: 20px auto 40px; max-width: 1000px;
        font-size: 0.75rem; color: #6b7fa8; backdrop-filter: blur(10px);
    }
    .status-bar-custom b { color: #22d3ee; margin-left: 4px; font-family: 'JetBrains Mono'; }

    /* Panels Styling */
    div[data-testid="stVerticalBlockBorderWrapper"] {
        background: rgba(10, 14, 28, 0.9) !important;
        border: 1px solid rgba(60, 130, 255, 0.25) !important;
        border-radius: 20px !important;
        padding: 25px !important;
        box-shadow: 0 15px 50px rgba(0,0,0,0.6) !important;
    }
    
    .panel-hdr { font-weight: 800; font-size: 1.1rem; margin-bottom: 25px; color: #fff; display: flex; align-items: center; gap: 10px; }

    /* Forms & Inputs */
    div[data-baseweb="textarea"] { background: #080c18 !important; border: 1px solid rgba(255,255,255,0.1) !important; border-radius: 12px !important; }
    textarea { color: #d4dff7 !important; font-family: 'JetBrains Mono' !important; font-size: 0.88rem !important; line-height: 1.6 !important; }
    
    /* Buttons */
    .stButton > button { border-radius: 12px !important; font-weight: 700 !important; cursor: pointer !important; transition: all 0.2s !important; }
    
    /* Main Audit Button */
    [key="audit_main_btn"] button {
        background: linear-gradient(135deg, #3b82f6, #22d3ee) !important;
        color: white !important; height: 3.8rem !important; font-size: 1.1rem !important;
        box-shadow: 0 6px 25px rgba(59, 130, 246, 0.4) !important; border: none !important; margin-top: 15px !important;
    }
    [key="audit_main_btn"] button:hover { transform: translateY(-3px); box-shadow: 0 10px 35px rgba(59, 130, 246, 0.6) !important; }

    /* Example Pills */
    [key^="ex_pill"] button {
        background: rgba(255,255,255,0.04) !important; color: #6b7fa8 !important; 
        border: 1px solid rgba(255,255,255,0.1) !important; border-radius: 99px !important;
        padding: 6px 18px !important; font-size: 0.75rem !important; margin-bottom: 10px !important;
    }
    [key^="ex_pill"] button:hover { color: #22d3ee !important; border-color: #22d3ee !important; background: rgba(34, 211, 238, 0.05) !important; }
</style>
""", unsafe_allow_html=True)

# 3. Initialization Logic
pk = (st.secrets.get("OG_PRIVATE_KEY") or os.environ.get("OG_PRIVATE_KEY") or "").strip()

# Better initialization with error reporting
@st.cache_resource
def init_og_client(_pk):
    if not _pk: return None, "Missing Private Key"
    try:
        # Test if it's a valid hex key
        if _pk.startswith("0x"): test_pk = _pk
        else: test_pk = "0x" + _pk
        
        c = og.Client(private_key=test_pk)
        return c, None
    except Exception as e:
        return None, str(e)

client, sdk_error = init_og_client(pk)

wallet_addr = "0x000...000"
balance = "0.000"

if pk:
    try:
        w3 = Web3(Web3.HTTPProvider("https://sepolia.base.org"))
        acct = w3.eth.account.from_key(pk)
        wallet_addr = acct.address
        # Real balance check
        OPG_TOKEN = "0x240b09731D96979f50B2C649C9CE10FcF9C7987F"
        ABI = [{"inputs":[{"name":"account","type":"address"}],"name":"balanceOf","outputs":[{"name":"","type":"uint256"}],"stateMutability":"view","type":"function"}]
        contract = w3.eth.contract(address=OPG_TOKEN, abi=ABI)
        raw_bal = contract.functions.balanceOf(wallet_addr).call()
        balance = "{:.3f}".format(raw_bal / 1e18)
    except Exception as e:
        st.sidebar.warning(f"Wallet check failed: {e}")

# 4. Header UI
st.markdown(f"""
<div class="title-area">
    <div class="badge-tee">TEE-Verified Proof Active</div>
    <div class="title-gradient">Security Auditor</div>
    <div style="color: #6b7fa8; font-size: 1.1rem; margin-top: 5px;">AI-powered security analyst on OpenGradient</div>
</div>

<div class="status-bar-custom">
    <div>Model: <b>GEMINI_2_0_FLASH</b></div>
    <div>Wallet: <b>{wallet_addr[:8]}...{wallet_addr[-6:]}</b></div>
    <div>Balance: <b>{balance} OPG</b></div>
    <div>Net: <b>Base Sepolia</b></div>
</div>
""", unsafe_allow_html=True)

# 5. Data & Samples
EXAMPLES = {
    "ERC-20 Example": "// SPDX-License-Identifier: MIT\npragma solidity ^0.8.20;\nimport \"@openzeppelin/contracts/token/ERC20/ERC20.sol\";\n\ncontract MyToken is ERC20 {\n    constructor() ERC20(\"RankoToken\", \"RNK\") {\n        _mint(msg.sender, 1000000 * 10**18);\n    }\n}",
    "Vulnerable Code": "// SPDX-License-Identifier: MIT\npragma solidity ^0.7.0;\n\ncontract Vulnerable {\n    mapping(address => uint256) public balances;\n    function withdraw(uint256 amount) public {\n        require(balances[msg.sender] >= amount);\n        (bool ok, ) = msg.sender.call{value: amount}(\"\");\n        require(ok);\n        balances[msg.sender] -= amount;\n    }\n}",
    "Reentrancy": "// SPDX-License-Identifier: MIT\npragma solidity ^0.8.0;\n\ncontract Bank {\n    mapping(address => uint) public balances;\n    function withdraw() public {\n        uint bal = balances[msg.sender];\n        require(bal > 0);\n        (bool sent,) = msg.sender.call{value: bal}(\"\");\n        require(sent);\n        balances[msg.sender] = 0;\n    }\n}"
}

# 6. Main App Grid
col1, col2 = st.columns(2, gap="large")

with col1:
    with st.container(border=True):
        st.markdown('<div class="panel-hdr">📝 Source Code</div>', unsafe_allow_html=True)
        
        # Example Pills
        cols_p = st.columns(3)
        if cols_p[0].button("ERC-20 Example", key="ex_pill_1"): st.session_state.editor = EXAMPLES["ERC-20 Example"]
        if cols_p[1].button("Vulnerable Code", key="ex_pill_2"): st.session_state.editor = EXAMPLES["Vulnerable Code"]
        if cols_p[2].button("Reentrancy", key="ex_pill_3"): st.session_state.editor = EXAMPLES["Reentrancy"]
        
        # Editor
        input_code = st.text_area("source_editor", value=st.session_state.get("editor", ""), height=450, key="editor_key", label_visibility="collapsed")
        
        # Audit Action
        if st.button("🔍 START SECURITY ANALYSIS", type="primary", key="audit_main_btn"):
            if sdk_error:
                st.error(f"❌ SDK Connection Failed: {sdk_error}")
                st.info("Check your OG_PRIVATE_KEY in Secrets and ensure it's a valid 64-char hex string.")
            elif not input_code:
                st.warning("⚠️ Please paste code first")
            else:
                with st.spinner("TEE Analysis in progress..."):
                    try:
                        p = "Audit this contract. Return JSON: {score: number, summary: string, vulnerabilities: [{title: string, severity: string, description: string, recommendation: string}]}"
                        r = client.llm.chat(
                            model=og.TEE_LLM.GEMINI_2_0_FLASH,
                            messages=[{"role":"system","content":p}, {"role":"user","content":input_code}],
                            x402_settlement_mode=og.x402SettlementMode.SETTLE_BATCH
                        )
                        content = r.chat_output.get("content", "")
                        if "```json" in content: content = content.split("```json")[1].split("```")[0]
                        elif "```" in content: content = content.split("```")[1].split("```")[0]
                        st.session_state.results = json.loads(content)
                        st.session_state.tx_p = getattr(r, "payment_hash", None)
                        st.rerun()
                    except Exception as e:
                        st.error(f"Audit failed: {e}")

with col2:
    with st.container(border=True):
        st.markdown('<div class="panel-hdr">📊 Analysis Report</div>', unsafe_allow_html=True)
        
        if "results" in st.session_state:
            res = st.session_state.results
            s_val = int(res.get("score" if "score" in res else "risk_score", 0))
            s_color = "#ef4444" if s_val > 70 else "#f97316" if s_val > 40 else "#10b981"
            
            st.markdown(f"""
                <div style="background:rgba(0,0,0,0.3); border-radius:18px; padding:35px; text-align:center; border:1px solid rgba(255,255,255,0.05); margin-bottom:2rem;">
                    <div style="font-size:0.85rem; color:#6b7fa8; text-transform:uppercase; letter-spacing:1.5px;">Security Risk Score</div>
                    <div style="font-size:4.5rem; font-weight:800; color:{s_color}; line-height:1;">{s_val}</div>
                    <p style="margin-top:25px; line-height:1.7; font-size:1rem;">{res.get('summary','')}</p>
                </div>
            """, unsafe_allow_html=True)
            
            for v in res.get("vulnerabilities" if "vulnerabilities" in res else "findings", []):
                with st.expander(f"⚠️ {v.get('title','Issue Found')}"):
                    st.write(v.get('description',''))
                    st.info(f"💡 Recommendation: {v.get('recommendation','')}")
            
            if st.session_state.get("tx_p"):
                st.markdown(f'<div style="text-align:center; margin-top:25px;"><a href="https://sepolia.basescan.org/tx/{st.session_state.tx_p}" target="_blank" style="color:#22d3ee; text-decoration:none; padding:12px 25px; border:1px solid rgba(34,211,238,0.3); border-radius:12px; background:rgba(34,211,238,0.06);">🔗 View On-Chain Proof ↗</a></div>', unsafe_allow_html=True)
        else:
            st.markdown("""
                <div style="text-align:center; padding-top:150px; opacity:0.3;">
                    <div style="font-size:5rem; margin-bottom:20px;">🛡️</div>
                    <div style="font-weight:700; font-size:1.2rem;">System Ready</div>
                    <div>Paste code to generate persistent report</div>
                </div>
            """, unsafe_allow_html=True)
