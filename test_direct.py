"""Direct LLM test with actual audit prompt."""
import os, opengradient as og

try:
    from dotenv import load_dotenv
    load_dotenv()
except: pass

private_key = os.environ.get("OG_PRIVATE_KEY", "")
client = og.Client(private_key=private_key)

# Simple system prompt (no Arabic, no special chars)
messages = [
    {
        "role": "system",
        "content": "You are a Solidity auditor. Reply with JSON only: {\"summary\":\"...\",\"risk_score\":0,\"vulnerabilities\":[],\"gas_optimizations\":[],\"best_practices\":[]}"
    },
    {
        "role": "user",
        "content": "Audit: pragma solidity ^0.8.0; contract T { address owner; constructor(){owner=msg.sender;} function withdraw() public { payable(msg.sender).transfer(address(this).balance); } }"
    }
]

print("Testing GPT_4_1 with audit prompt...")
try:
    r = client.llm.chat(
        model=og.TEE_LLM.GPT_4_1_2025_04_14,
        messages=messages,
        max_tokens=500,
        temperature=0.1,
        x402_settlement_mode=og.x402SettlementMode.SETTLE_BATCH
    )
    print(f"SUCCESS!")
    print(f"Response: {(r.chat_output or {}).get('content', '')[:500]}")
    print(f"Payment hash: {r.payment_hash}")
except Exception as e:
    print(f"FAIL: {e}")

print("\nTesting GEMINI_2_5_FLASH with audit prompt...")
try:
    r = client.llm.chat(
        model=og.TEE_LLM.GEMINI_2_5_FLASH,
        messages=messages,
        max_tokens=500,
        temperature=0.1,
        x402_settlement_mode=og.x402SettlementMode.SETTLE_BATCH
    )
    print(f"SUCCESS!")
    print(f"Response: {(r.chat_output or {}).get('content', '')[:500]}")
except Exception as e:
    print(f"FAIL: {e}")
