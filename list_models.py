import opengradient as og
print("Available TEE_LLM models:")
for attr in dir(og.TEE_LLM):
    if not attr.startswith("_"):
        print(f"{attr}: {getattr(og.TEE_LLM, attr)}")
