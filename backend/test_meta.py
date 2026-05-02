import sys
import os
sys.path.append(os.getcwd())
from app.services.data_service import get_dataframe, get_metadata
try:
    print("Loading dataframe...")
    df = get_dataframe()
    print("Dataframe loaded.")
    meta = get_metadata(df)
    print("Metadata generated.")
    print(meta.keys())
except Exception as e:
    print(f"Error: {e}")
