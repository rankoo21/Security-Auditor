import opengradient as og
try:
    for m in og.TEE_LLM:
        print(f"{m.name}: {m.value}")
except:
    print("Cannot iterate TEE_LLM directly")
