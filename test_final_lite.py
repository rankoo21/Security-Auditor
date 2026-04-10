import os, asyncio, opengradient as og
from dotenv import load_dotenv

load_dotenv()

PRIVATE_KEY = os.environ.get("OG_PRIVATE_KEY")
OG_LLM_SERVER = "https://3.15.214.21"

messages = [
    {
        "role": "system",
        "content": "You are a Solidity auditor. Reply with JSON only: {\"summary\":\"...\",\"risk_score\":0,\"vulnerabilities\":[],\"gas_optimizations\":[],\"best_practices\":[]}"
    },
    {
        "role": "user",
        "content": "Audit: pragma solidity ^0.8.0; contract T { }"
    }
]

async def run_test():
    if not PRIVATE_KEY:
        print("Set OG_PRIVATE_KEY first!")
        return

    print("Testing GEMINI_2_5_FLASH_LITE (The Cheapest)...")
    try:
        llm = og.LLM(private_key=PRIVATE_KEY, llm_server_url=OG_LLM_SERVER)
        r = await llm.chat(
            model=og.TEE_LLM.GEMINI_2_5_FLASH_LITE,
            messages=messages,
            max_tokens=600,
            temperature=0.1,
            x402_settlement_mode=og.x402SettlementMode.BATCH_HASHED
        )
        print("SUCCESS!")
        # Extra chat output content
        raw = getattr(r, "chat_output", None)
        if isinstance(raw, dict): content = raw.get("content", "")
        elif hasattr(raw, "content"): content = getattr(raw, "content")
        else: content = str(raw)
        
        print(f"Response: {content}")
    except Exception as e:
        print(f"FAIL: {e}")

if __name__ == "__main__":
    asyncio.run(run_test())
