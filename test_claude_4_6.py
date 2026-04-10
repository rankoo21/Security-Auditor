import os
import asyncio
import opengradient as og
from dotenv import load_dotenv

load_dotenv()

PRIVATE_KEY = os.environ.get("OG_PRIVATE_KEY")
OG_LLM_SERVER = "https://3.15.214.21"

async def test():
    if not PRIVATE_KEY:
        print("No private key found")
        return

    try:
        llm = og.LLM(
            private_key=PRIVATE_KEY,
            llm_server_url=OG_LLM_SERVER
        )
        
        print("Testing CLAUDE_SONNET_4_6...")
        result = await llm.chat(
            model=og.TEE_LLM.CLAUDE_SONNET_4_6,
            messages=[{"role": "user", "content": "Hello, are you Claude Sonnet 4.6?"}],
            max_tokens=100,
            x402_settlement_mode=og.x402SettlementMode.BATCH_HASHED
        )
        
        print(f"Result: {result}")
        raw_output = getattr(result, "chat_output", None)
        if isinstance(raw_output, dict):
            print(f"Content: {raw_output.get('content')}")
        elif hasattr(raw_output, "content"):
            print(f"Content: {getattr(raw_output, 'content')}")
        else:
            print(f"Raw: {raw_output}")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(test())
