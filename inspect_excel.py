import pandas as pd
import os

# file_path = r'd:\RA\assets\Primer-Database.xlsx'
file_path = r'C:\Users\tahay\Desktop\RA\assets\Primer-Database.xlsx'


try:
    if not os.path.exists(file_path):
        print(f"Error: File not found at {file_path}")
    else:
        df = pd.read_excel(file_path, engine='openpyxl')
        print("Columns:", df.columns.tolist())
        print("First 10 rows:")
        print(df.head(10).to_string())
except Exception as e:
    print(f"Error reading excel: {e}")
