import pandas as pd
import re
from datetime import datetime

# Read the CSV, skipping non-table lines
def find_table_start(filename):
    with open(filename, encoding='utf-8') as f:
        for i, line in enumerate(f):
            if line.strip().startswith('---|'):
                return i
    return 0

def clean_amount(val):
    if not val or val.strip() == '':
        return ''
    val = val.replace('.', '').replace(' ', '').replace(',', '.')
    if val.endswith('-'):
        val = '-' + val[:-1]
    try:
        return float(val)
    except Exception:
        return val

def clean_date(val):
    for fmt in ("%d.%m.%y", "%d/%m/%Y", "%d.%m.%Y", "%d/%m/%y"):  # add more as needed
        try:
            return datetime.strptime(val, fmt).strftime("%Y-%m-%d")
        except Exception:
            continue
    return val

def clean_account(val):
    # Accepts E, N, MT, U, I, or digits, leading zeros allowed
    m = re.match(r'^(E\d+|N\d+|MT\d+|U\d+|I\d+|\d+)', val)
    return m.group(0) if m else val

def clean_id(val):
    m = re.search(r'ID: ?([0-9]{10,13})', val)
    return m.group(1) if m else ''

def process_csv(input_csv, output_xlsx):
    table_start = find_table_start(input_csv)
    df = pd.read_csv(input_csv, sep='|', skiprows=table_start+1, engine='python')
    df = df.applymap(lambda x: x.strip() if isinstance(x, str) else x)
    # Clean columns
    if 'ACCOUNT NAME' in df.columns:
        df['ACCOUNT'] = df['ACCOUNT NAME'].apply(clean_account)
    if 'LAST VISIT' in df.columns:
        df['LAST VISIT'] = df['LAST VISIT'].apply(clean_date)
    if 'LAST PAYMENT' in df.columns:
        df['LAST PAYMENT'] = df['LAST PAYMENT'].apply(clean_amount)
    for col in ['CURRENT', '30 DAYS', '60 DAYS', '90 DAYS', '120 DAYS', '150 DAYS']:
        if col in df.columns:
            df[col] = df[col].apply(clean_amount)
    if 'OUTS' in df.columns:
        df['ID NUMBER'] = df['OUTS'].apply(clean_id)
    # Reorder columns for clarity
    cols = [c for c in ['ACCOUNT','ACCOUNT NAME','LAST VISIT','LAST PAYMENT','CURRENT','30 DAYS','60 DAYS','90 DAYS','120 DAYS','150 DAYS','ID NUMBER','OUTS','LAST RECEIPT','CLAIM','STATUS'] if c in df.columns]
    df = df[cols]
    df.to_excel(output_xlsx, index=False)

if __name__ == "__main__":
    process_csv('reports 2_2.csv', 'p1-3.xlsx')
