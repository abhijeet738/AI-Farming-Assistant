"""
Diagnostic script to inspect the structure of the merged_document.pkl file.
Run: python inspect_pkl.py
"""
import pickle
import sys

PKL_PATH = "/Users/abhijeetraj/Downloads/merged_document.pkl"

print(f"Loading: {PKL_PATH}\n")

with open(PKL_PATH, "rb") as f:
    data = pickle.load(f)

# ── Type ──────────────────────────────────────────────────────────────────────
print(f"Top-level type : {type(data)}")
print(f"Length         : {len(data) if hasattr(data, '__len__') else 'N/A'}")

# ── If it's a list ─────────────────────────────────────────────────────────────
if isinstance(data, list):
    print(f"\nFirst element type : {type(data[0])}")
    print("\n── Sample [0] ──")
    print(repr(data[0])[:800])
    if len(data) > 1:
        print("\n── Sample [1] ──")
        print(repr(data[1])[:400])

# ── If it's a dict ─────────────────────────────────────────────────────────────
elif isinstance(data, dict):
    print(f"\nKeys : {list(data.keys())[:20]}")
    first_key = list(data.keys())[0]
    print(f"\n── Sample['{first_key}'] ──")
    print(repr(data[first_key])[:800])

# ── If it's a DataFrame ────────────────────────────────────────────────────────
else:
    try:
        import pandas as pd
        if isinstance(data, pd.DataFrame):
            print(f"\nColumns : {list(data.columns)}")
            print("\n── Head(2) ──")
            print(data.head(2).to_string())
    except ImportError:
        pass
    print("\n── Raw repr ──")
    print(repr(data)[:800])

print("\n✅ Inspection complete.")
