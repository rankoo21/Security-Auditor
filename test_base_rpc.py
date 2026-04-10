import os, asyncio, opengradient as og
from dotenv import load_dotenv

load_dotenv()

PRIVATE_KEY = os.environ.get("OG_PRIVATE_KEY")
BASE_RPC = "https://sepolia.base.org"

async def test():
    print("Testing OG 0.9.4 with Base Sepolia RPC...")
    try:
        # Note: tee_registry might be different if on base.
        llm = og.LLM(private_key=PRIVATE_KEY, rpc_url=BASE_RPC)
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
