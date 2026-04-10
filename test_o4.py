import os, asyncio, opengradient as og
from dotenv import load_dotenv

load_dotenv()

PRIVATE_KEY = os.environ.get("OG_PRIVATE_KEY")
OG_LLM_SERVER = "https://3.15.214.21"

messages = [{"role": "user", "content": "HI"}]

async def run_test():
    if not PRIVATE_KEY:
        print("No private key found")
        return

    print("Testing O4_MINI...")
    try:
        llm = og.LLM(private_key=PRIVATE_KEY, llm_server_url=OG_LLM_SERVER)
        r = await llm.chat(
            model=og.TEE_LLM.O4_MINI,
            messages=messages,
            max_tokens=2,
            temperature=0.7,
            x402_settlement_mode=og.x402SettlementMode.BATCH_HASHED
        )
        print(f"SUCCESS! -> {r}")
    except Exception as e:
        print(f"FAIL: {e}")

if __name__ == "__main__":
    asyncio.run(run_test())
