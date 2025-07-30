import pandas as pd
# Read the cleaned CSV and save as XLSX
csv_file = 'reports 2_2.csv'
xlsx_file = 'p1-3.xlsx'
df = pd.read_csv(csv_file, sep='|', engine='python')
df = df.applymap(lambda x: x.strip() if isinstance(x, str) else x)
df.to_excel(xlsx_file, index=False)
print('Done: p1-3.xlsx created.')
