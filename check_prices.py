import opengradient as og
import inspect

for name, model in inspect.getmembers(og.TEE_LLM):
    if not name.startswith("__") and not inspect.ismethod(model) and not inspect.isfunction(model):
        try:
            # Check for pricing attributes if they exist
            print(f"{name}: {model}")
            # Try to see if there's a cost or price attr on the model object itself
            attrs = [a for a in dir(model) if not a.startswith("_")]
            if attrs:
                print(f"  Attributes: {attrs}")
        except:
            pass
