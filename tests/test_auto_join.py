
from src.services.data_tools import DataAnalyzer
import pandas as pd

def test_auto_join():
    print("Testing Auto-Join...")
    analyzer = DataAnalyzer(data_dir="data")
    
    result = analyzer.get_top_n(
        "FATO_AVCURSOS",
        metric="satisfacao",
        n=5,
        group_by="COD_CURSO",
        ascending=False
    )
    
    print("Columns:", result.columns.tolist())
    print(result.head())
    
    if 'CURSO' in result.columns:
        print("SUCCESS: CURSO found!")
        print(result[['COD_CURSO', 'CURSO', 'satisfacao_%']].head())
    else:
        print("FAILURE: CURSO not found!")
        print("Columns found:", result.columns.tolist())

if __name__ == "__main__":
    test_auto_join()
