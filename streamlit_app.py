import streamlit as st
import opengradient as og
import os
import json
from web3 import Web3

# 1. Page Config
st.set_page_config(page_title="AI Security Auditor", page_icon="🛡️", layout="wide")

# 2. CSS - The "Skin" of Localhost (Clean & Safe)
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;800&family=JetBrains+Mono&display=swap');

    .stApp { background: #04060d; color: #d4dff7; font-family: 'Outfit', sans-serif; }
    [data-testid="stHeader"] { visibility: hidden; }
    
    /* Header Area */
    .header-style { text-align: center; padding: 20px 0; }
    .title-grad { 
        font-size: 3rem; font-weight: 800; 
        background: linear-gradient(135deg, #60a5fa, #22d3ee, #10b981);
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;
    }
    
    /* Info Bar (The Gray Bar) */
    .st-info-bar {
        background: rgba(255,255,255,0.03); border: 1px solid rgba(255,255,255,0.08);
        border-radius: 10px; padding: 12px; margin: 10px auto 30px; display: flex; 
        justify-content: center; gap: 30px; font-size: 0.8rem; color: #6b7fa8;
    }
    .st-info-bar b { color: #22d3ee; font-family: 'JetBrains Mono'; }

    /* Panels */
    [data-testid="stVerticalBlock"] > div > div > div[data-testid="stVerticalBlock"] {
        background: rgba(10, 14, 28, 0.95);
        border: 1px solid rgba(60, 130, 255, 0.2);
        border-radius: 20px; padding: 20px;
        box-shadow: 0 10px 40px rgba(0,0,0,0.5);
    }
    
    /* Buttons */
    .stButton > button { border-radius: 10px !important; }
    button[kind="primary"] {
        background: linear-gradient(135deg, #3b82f6, #22d3ee) !important;
        border: none !important; font-weight: 800 !important; color: white !important;
        height: 3.5rem !important; width: 100% !important;
    }
    button[kind="secondary"] {
        background: rgba(255,255,255,0.05) !important; color: #22d3ee !important;
        border-radius: 99px !important; border: 1px solid rgba(34,211,238,0.2) !important;
    }
</style>
""", unsafe_allow_html=True)

# 3. Security Check (Wallet Logic)
pk = st.secrets.get("OG_PRIVATE_KEY") or os.environ.get("OG_PRIVATE_KEY")
w_addr = "0x00...00"
w_bal = "0.00"
client = None

if not pk:
    st.sidebar.error("❌ OG_PRIVATE_KEY missing in Streamlit Secrets!")
    st.sidebar.info("Add it in your Dashboard -> Settings -> Secrets")
else:
    try:
        client = og.Client(private_key=pk)
        w3 = Web3(Web3.HTTPProvider("https://sepolia.base.org"))
        acct = w3.eth.account.from_key(pk)
        w_addr = acct.address
        # Simplified Balance
        OPG = "0x240b09731D96979f50B2C649C9CE10FcF9C7987F"
        ABI = [{"inputs":[{"name":"account","type":"address"}],"name":"balanceOf","outputs":[{"name":"","type":"uint256"}],"stateMutability":"view","type":"function"}]
        c_opg = w3.eth.contract(address=OPG, abi=ABI)
        w_bal = round(c_opg.functions.balanceOf(w_addr).call() / 1e18, 3)
    except Exception as e:
        st.sidebar.warning(f"Connection Error: {e}")

# 4. Header UI
st.markdown('<div class="header-style"><div class="title-grad">Security Auditor</div><div style="color:#6b7fa8;">AI-Powered TEE Security Analysis</div></div>', unsafe_allow_html=True)
st.markdown(f'''
<div class="st-info-bar">
    <div>Model: <b>GEMINI_2_0_FLASH</b></div>
    <div>Wallet: <b>{w_addr[:8]}...{w_addr[-6:]}</b></div>
    <div>Balance: <b>{w_bal} OPG</b></div>
    <div>Network: <b>Base Sepolia</b></div>
</div>
''', unsafe_allow_html=True)

# 5. Data Examples
EXAMPLES = {
    "ERC-20": "// SPDX-License-Identifier: MIT\npragma solidity ^0.8.20;\nimport \"@openzeppelin/contracts/token/ERC20/ERC20.sol\";\ncontract MyToken is ERC20 { constructor() ERC20(\"Test\", \"TST\") { _mint(msg.sender, 1000 * 10**18); } }",
    "Vulnerable": "// SPDX-License-Identifier: MIT\npragma solidity ^0.7.0;\ncontract Vulnerable { mapping(address => uint) public balances; function withdraw() public { uint bal = balances[msg.sender]; require(bal > 0); (bool s,) = msg.sender.call{value: bal}(\"\"); require(s); balances[msg.sender] = 0; } }"
}

# 6. APP GRID
c1, c2 = st.columns(2, gap="large")

with c1:
    st.write("### 📝 Source Code")
    # Pills row
    p1, p2 = st.columns(2)
    if p1.button("Load ERC-20 Example"): st.session_state.ed = EXAMPLES["ERC-20"]
    if p2.button("Load Vulnerable Code"): st.session_state.ed = EXAMPLES["Vulnerable"]
    
    # Editor
    code_in = st.text_area("in", value=st.session_state.get("ed", ""), height=450, label_visibility="collapsed")
    
    if st.button("🔍 START SECURITY AUDIT", type="primary"):
        if not client: st.error("SDK not initialized. Check Secrets.")
        elif not code_in: st.warning("Paste code first.")
        else:
            with st.spinner("Analyzing on TEE..."):
                try:
                    p = "Audit this code. Return JSON: {score: number, summary: string, findings: [{title, severity, desc, rec}]}"
                    r = client.llm.chat(model=og.TEE_LLM.GEMINI_2_0_FLASH, messages=[{"role":"system","content":p}, {"role":"user","content":code_in}], x402_settlement_mode=og.x402SettlementMode.SETTLE_BATCH)
                    content = r.chat_output.get("content", "")
                    if "```json" in content: content = content.split("```json")[1].split("```")[0]
                    st.session_state.res = json.loads(content)
                    st.session_state.tx = getattr(r, "payment_hash", None)
                    st.rerun()
                except Exception as e: st.error(f"Error: {e}")

with c2:
    st.write("### 📊 Audit Report")
    if "res" in st.session_state:
        res = st.session_state.res
        score = int(res.get("score", 0))
        clr = "#ef4444" if score > 70 else "#f97316" if score > 40 else "#10b981"
        
        st.markdown(f'''
            <div style="background:rgba(0,0,0,0.2); border-radius:15px; padding:30px; text-align:center; border:1px solid rgba(255,255,255,0.05);">
                <div style="font-size:0.8rem; color:#6b7fa8;">RISK SCORE</div>
                <div style="font-size:4.5rem; font-weight:800; color:{clr}; line-height:1;">{score}</div>
                <p style="margin-top:20px; font-size:0.95rem;">{res.get('summary','')}</p>
            </div>
        ''', unsafe_allow_html=True)
        
        for f in res.get("findings", []):
            with st.expander(f"⚠️ {f.get('title')}"):
                st.write(f.get('desc'))
                st.info(f"💡 Recommendation: {f.get('rec')}")
        
        if st.session_state.get("tx"):
            st.markdown(f'<div style="text-align:center; margin-top:20px;"><a href="https://sepolia.basescan.org/tx/{st.session_state.tx}" target="_blank" style="color:#22d3ee; text-decoration:none; padding:10px 20px; border:1px solid rgba(34,211,238,0.2); border-radius:12px;">🔗 View On-Chain Proof</a></div>', unsafe_allow_html=True)
    else:
        st.info("System Ready. Paste code to generate report.")
