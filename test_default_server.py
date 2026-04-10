import os, asyncio, opengradient as og
from dotenv import load_dotenv

load_dotenv()

PRIVATE_KEY = os.environ.get("OG_PRIVATE_KEY")

messages = [{"role": "user", "content": "HI"}]

async def run_test():
    if not PRIVATE_KEY:
        print("Set OG_PRIVATE_KEY first!")
        return

    print("Testing GEMINI_2_5_FLASH_LITE with NO custom server URL...")
    try:
        # Default initialization
        llm = og.LLM(private_key=PRIVATE_KEY)
        r = await llm.chat(
            model=og.TEE_LLM.GEMINI_2_5_FLASH_LITE,
            messages=messages,
            max_tokens=60,
            temperature=0.7,
            x402_settlement_mode=og.x402SettlementMode.BATCH_HASHED
        )
        print(f"SUCCESS! -> {r}")
    except Exception as e:
        print(f"FAIL: {e}")

if __name__ == "__main__":
    asyncio.run(run_test())
