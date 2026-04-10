import os, asyncio, opengradient as og
from dotenv import load_dotenv

load_dotenv()

PRIVATE_KEY = os.environ.get("OG_PRIVATE_KEY")
OG_LLM_SERVER = "https://3.15.214.21"

async def test_all():
    if not PRIVATE_KEY:
        print("No private key")
        return

    llm = og.LLM(private_key=PRIVATE_KEY, llm_server_url=OG_LLM_SERVER)
    
    models = []
    for attr in dir(og.TEE_LLM):
        if not attr.startswith("_"):
            try:
                models.append((attr, getattr(og.TEE_LLM, attr)))
            except: pass

    print(f"Testing {len(models)} models with balance of 0.1841 OPG...")
    
    for name, model in models:
        print(f"Testing {name}... ", end="", flush=True)
        try:
            r = await llm.chat(
                model=model,
                messages=[{"role": "user", "content": "HI"}],
                max_tokens=2,
                temperature=0,
                x402_settlement_mode=og.x402SettlementMode.BATCH_HASHED
            )
            print("OK!")
        except Exception as e:
            err = str(e)
            if "402" in err:
                print("FAIL: 402 Payment Required")
            else:
                print(f"FAIL: {err[:50]}...")

if __name__ == "__main__":
    asyncio.run(test_all())
