"""Test all available models to find one that works."""
import os, opengradient as og

private_key = os.environ.get("OG_PRIVATE_KEY", "")
if not private_key:
    from dotenv import load_dotenv
    load_dotenv()
    private_key = os.environ.get("OG_PRIVATE_KEY", "")

client = og.Client(private_key=private_key)

# Try all known models
models_to_try = []
for attr in dir(og.TEE_LLM):
    if not attr.startswith("_"):
        try:
            models_to_try.append((attr, getattr(og.TEE_LLM, attr)))
        except:
            pass

print(f"Found {len(models_to_try)} models to test:\n")

for name, model in models_to_try:
    print(f"  {name}... ", end="", flush=True)
    try:
        r = client.llm.chat(
            model=model,
            messages=[
                {"role": "system", "content": "Reply OK"},
                {"role": "user", "content": "test"}
            ],
            max_tokens=10,
            temperature=0,
            x402_settlement_mode=og.x402SettlementMode.SETTLE_BATCH
        )
        content = (r.chat_output or {}).get("content", "")
        if content:
            print(f"OK! -> {content.strip()[:30]}")
        else:
            print(f"EMPTY response")
    except Exception as e:
        err = str(e)[:80]
        print(f"FAIL: {err}")

print("\nDone!")
