import opengradient as og
try:
    print(f"Client exist? {og.Client is not None}")
except Exception as e:
    print(f"Error: {e}")
