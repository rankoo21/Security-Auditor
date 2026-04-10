import os, asyncio, opengradient as og
from dotenv import load_dotenv

load_dotenv()

PRIVATE_KEY = os.environ.get("OG_PRIVATE_KEY")

async def test():
    print("Testing OG 0.9.4 with default LLM(pk)...")
    try:
        llm = og.LLM(private_key=PRIVATE_KEY)
        r = await llm.chat(
            model=og.TEE_LLM.GEMINI_2_5_FLASH_LITE,
            messages=[{"role": "user", "content": "HI"}],
            max_tokens=2,
            x402_settlement_mode=og.x402SettlementMode.BATCH_HASHED
        )
        print(f"SUCCESS! -> {r}")
    except Exception as e:
        print(f"FAIL: {e}")

if __name__ == "__main__":
    asyncio.run(test())
