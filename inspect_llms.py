import opengradient as og
import inspect

print("TEE_LLM members:")
for name, value in inspect.getmembers(og.TEE_LLM):
    if not name.startswith("__") and not inspect.ismethod(value) and not inspect.isfunction(value):
        print(f"{name}: {value}")
