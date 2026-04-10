import opengradient as og
print("Available Models in 0.9.4:")
for a in dir(og.TEE_LLM):
    if not a.startswith("_"):
        try:
            print(f"  - {a}: {getattr(og.TEE_LLM, a).value}")
        except: pass
