import pandas as pd
import numpy as np

EXPECTED_COLUMNS = [
    'Account_ID','Account_Name','Account_Type','Last_Visit','Last_Receipt_Payment',
    'Current','30_Days','60_Days','90_Days','120_Days','150_Days','Outstanding',
    'Status','ID_Number','Claim'
]
MANDATORY_FIELDS = ['Account_ID', 'Account_Name', 'ID_Number']

def clean_page14():
    df = pd.read_csv('page14.csv', dtype=str)
    # Ensure all columns are present
    df = df.reindex(columns=EXPECTED_COLUMNS)
    # Fill missing mandatory fields with 'UNKNOWN'
    for field in MANDATORY_FIELDS:
        df[field] = df[field].replace({np.nan: 'UNKNOWN', '': 'UNKNOWN'})
    # Remove duplicate Account_ID + ID_Number
    df = df.drop_duplicates(subset=['Account_ID', 'ID_Number'])
    # Fix numeric columns: replace non-numeric with 0.00
    for col in ['Current','30_Days','60_Days','90_Days','120_Days','150_Days','Outstanding']:
        df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0.00).round(2)
    # Fix date columns: replace invalid with '1900-01-01'
    for col in ['Last_Visit','Last_Receipt_Payment']:
        df[col] = pd.to_datetime(df[col], errors='coerce').dt.strftime('%Y-%m-%d')
        df[col] = df[col].replace('NaT', '1900-01-01')
    # Save cleaned file
    df.to_csv('page14_cleaned.csv', index=False)
    print('page14_cleaned.csv generated.')

if __name__ == "__main__":
    clean_page14()
