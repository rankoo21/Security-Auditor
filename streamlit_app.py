import streamlit as st
import opengradient as og
import os
import json
from web3 import Web3

# 1. Page Config
st.set_page_config(page_title="AI Smart Contract Auditor", page_icon="🛡️", layout="wide")

try:
    from dotenv import load_dotenv
    load_dotenv()
except:
    pass

# 2. Key & Logic Initialization
def get_secret(k):
    try: return st.secrets.get(k)
    except: return None

pk = get_secret("OG_PRIVATE_KEY") or os.environ.get("OG_PRIVATE_KEY")
if pk:
    pk = pk.strip()
    if not pk.startswith("0x") and len(pk) == 64: pk = "0x" + pk

# 3. Premium CSS Injection
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;800&family=JetBrains+Mono&display=swap');

/* Main Background */
.stApp {
    background: radial-gradient(circle at 50% 0%, #1a2238 0%, #04060d 100%) !important;
    color: #d4dff7 !important;
    font-family: 'Outfit', sans-serif !important;
}

/* Hide Streamlit Header */
[data-testid="stHeader"] { visibility: hidden; height: 0px; }

/* Sidebar */
section[data-testid="stSidebar"] {
    background-color: rgba(10, 14, 28, 0.95) !important;
    border-right: 1px solid rgba(60, 130, 255, 0.1);
}

/* Title Gradient */
.title-grad {
    text-align: center;
    font-size: 3.5rem;
    font-weight: 800;
    letter-spacing: -1px;
    background: linear-gradient(135deg, #60a5fa, #22d3ee, #10b981);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    margin: 20px 0 10px 0;
    filter: drop-shadow(0 0 15px rgba(96, 165, 250, 0.3));
}

/* Status Banner */
.status-box {
    background: rgba(255, 255, 255, 0.03);
    backdrop-filter: blur(12px);
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 16px;
    padding: 15px 25px;
    margin: 0 auto 40px;
    display: flex;
    justify-content: space-around;
    align-items: center;
    gap: 20px;
    font-size: 0.85rem;
    color: #94a3b8;
    max-width: 1000px;
    box-shadow: inset 0 0 20px rgba(0,0,0,0.2);
}
.status-item b { color: #60a5fa; font-weight: 600; }

/* Containers (Glassmorphism) */
div[data-testid="stVerticalBlockBorderWrapper"] {
    background: rgba(15, 23, 42, 0.6) !important;
    backdrop-filter: blur(16px) !important;
    border: 1px solid rgba(148, 163, 184, 0.1) !important;
    border-radius: 24px !important;
    padding: 24px !important;
    box-shadow: 0 10px 30px -10px rgba(0,0,0,0.5) !important;
    transition: all 0.3s ease;
}
div[data-testid="stVerticalBlockBorderWrapper"]:hover {
    border-color: rgba(96, 165, 250, 0.3) !important;
    transform: translateY(-2px);
}

/* Text Inputs */
.stTextArea textarea {
    background: rgba(2, 6, 23, 0.5) !important;
    border: 1px solid rgba(148, 163, 184, 0.1) !important;
    border-radius: 12px !important;
    color: #e2e8f0 !important;
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 0.9rem !important;
}
.stTextArea textarea:focus {
    border-color: #60a5fa !important;
    box-shadow: 0 0 0 1px #60a5fa !important;
}

/* Buttons */
.stButton button {
    border-radius: 12px !important;
    font-weight: 600 !important;
    text-transform: uppercase !important;
    letter-spacing: 0.5px !important;
    transition: all 0.2s ease !important;
}
.stButton button[kind="primary"] {
    background: linear-gradient(135deg, #3b82f6, #2563eb) !important;
    border: none !important;
    box-shadow: 0 4px 15px rgba(37, 99, 235, 0.4) !important;
}
.stButton button[kind="primary"]:hover {
    transform: scale(1.02);
    box-shadow: 0 6px 20px rgba(37, 99, 235, 0.6) !important;
}

/* Subheaders */
h3 {
    color: #f1f5f9 !important;
    font-weight: 700 !important;
    margin-bottom: 20px !important;
}
</style>
""", unsafe_allow_html=True)

# 4. Global Variables
wa = "0x00...00"
wb = "0.00"
client = None

if pk:
    try:
        # og.LLM for 0.9.4
        llm_client = og.LLM(private_key=pk)
        w3 = Web3(Web3.HTTPProvider("https://sepolia.base.org"))
        acct = w3.eth.account.from_key(pk)
        wa = acct.address
        # Balance
        OPG = "0x240b09731D96979f50B2C649C9CE10FcF9C7987F"
        ABI = [{"inputs":[{"name":"account","type":"address"}],"name":"balanceOf","outputs":[{"name":"","type":"uint256"}],"stateMutability":"view","type":"function"}]
        contract = w3.eth.contract(address=OPG, abi=ABI)
        wb = round(contract.functions.balanceOf(wa).call() / 1e18, 3)
    except Exception as e:
        st.sidebar.error(f"Init Error: {e}")

# 5. Model Selection
models = {
    "Gemini 2.5 Flash Lite": og.TEE_LLM.GEMINI_2_5_FLASH_LITE,
    "Gemini 2.5 Flash": og.TEE_LLM.GEMINI_2_5_FLASH,
    "Claude Sonnet 4.6": og.TEE_LLM.CLAUDE_SONNET_4_6,
    "GPT-4 (OpenGradient)": og.TEE_LLM.GPT_4_1_2025_04_14
}
selected_model_name = st.sidebar.selectbox("Choose AI Model", list(models.keys()))
active_model = models[selected_model_name]

# 6. Header UI
st.markdown('<div class="title-grad">Security Auditor AI</div>', unsafe_allow_html=True)
st.markdown(f'''
<div class="status-box">
    <div class="status-item">Wallet: <b>{wa[:6]}...{wa[-4:]}</b></div>
    <div class="status-item">Balance: <b>{wb} OPG</b></div>
    <div class="status-item">Network: <b>Base Sepolia</b></div>
    <div class="status-item">Model: <b>{selected_model_name}</b></div>
</div>
''', unsafe_allow_html=True)

# 7. Content Grid
c1, c2 = st.columns(2, gap="large")

with c1:
    with st.container(border=True):
        st.subheader("📝 Source Code")
        if st.button("Load ERC-20"):
            st.session_state.code = "// ERC-20 Example\npragma solidity ^0.8.0;\ncontract Token { }"
        
        u_code = st.text_area("input", value=st.session_state.get("code", ""), height=400, label_visibility="collapsed")
        
        if st.button("🔍 SCAN SMART CONTRACT", type="primary"):
            if not llm_client: st.error("SDK Error: Check Private Key")
            elif not u_code: st.warning("Paste code")
            else:
                with st.spinner(f"Analyzing with {selected_model_name} on TEE..."):
                    try:
                        resp = llm_client.chat(
                            model=active_model, 
                            messages=[{"role":"user","content":u_code}],
                            max_tokens=800,
                            x402_settlement_mode=og.x402SettlementMode.BATCH_HASHED
                        )
                        st.session_state.rep = resp.chat_output.get("content", "Error parsing output")
                        st.rerun()
                    except Exception as e: st.error(str(e))

with c2:
    with st.container(border=True):
        st.subheader("📊 Security Report")
        if "rep" in st.session_state:
            try:
                # Clean and parse JSON
                raw_json = st.session_state.rep
                if "```json" in raw_json:
                    raw_json = raw_json.split("```json")[1].split("```")[0].strip()
                elif "```" in raw_json:
                    raw_json = raw_json.split("```")[1].strip()
                
                report = json.loads(raw_json)
                
                # Header Summary
                st.markdown(f"**Assessment:** {report.get('summary', 'Audit completed.')}")
                
                # Risk Score with Color
                score = report.get('risk_score', 0)
                color = "#10b981" if score < 30 else "#f59e0b" if score < 70 else "#ef4444"
                st.markdown(f"Risk Score: <span style='color:{color}; font-size: 1.5rem; font-weight: 800;'>{score}/100</span>", unsafe_allow_html=True)
                
                # Vulnerabilities
                st.markdown("---")
                st.markdown("#### 🛡️ Vulnerabilities")
                vulns = report.get('vulnerabilities', [])
                if not vulns:
                    st.success("No high-risk vulnerabilities detected.")
                else:
                    for v in vulns:
                        sev = v.get('severity', 'low').lower()
                        sev_color = "#ef4444" if sev in ['critical','high'] else "#f59e0b" if sev == 'medium' else "#3b82f6"
                        with st.expander(f"[{sev.upper()}] {v.get('title', 'Issue')}"):
                            st.markdown(f"**Description:** {v.get('description', '')}")
                            st.markdown(f"**Location:** `{v.get('line_hint', 'N/A')}`")
                            st.info(f"**Fix:** {v.get('recommendation', '')}")
                
                # Best Practices
                st.markdown("---")
                st.markdown("#### ✅ Best Practices")
                for p in report.get('best_practices', []):
                    st.write(f"- {p.get('status','').upper()} | **{p.get('title','')}**: {p.get('note','')}")

            except Exception as e:
                # Fallback to raw if parsing fails
                st.warning("Could not parse structured report. Showing raw output:")
                st.markdown(f"```json\n{st.session_state.rep}\n```")
        else:
            st.info("Results will appear here. No scan performed yet.")
