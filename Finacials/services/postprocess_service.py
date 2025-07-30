import re
import csv

def clean_account_row(raw_row):
    # Try to extract account id, name, date, amount, and ID number from a messy row
    if isinstance(raw_row, str):
        fields = [f.strip() for f in re.split(r',|\s{2,}', raw_row) if f.strip()]
    else:
        fields = [str(f).strip() for f in raw_row if str(f).strip()]
    # Find account id (first 6+ digit/letter string)
    account_id = ''
    for f in fields:
        m = re.match(r'([A-Z0-9]{6,})', f.upper())
        if m:
            account_id = m.group(1)
            break
    # Find name (next field that is not a number/date)
    name = ''
    for f in fields[1:]:
        if not re.match(r'^[0-9.,-]+$', f) and not re.match(r'\d{2}\.\d{2}\.\d{2,4}', f):
            name = f
            break
    # Find date
    date = ''
    for f in fields:
        if re.match(r'\d{2}\.\d{2}\.\d{2,4}', f):
            date = f
            break
    # Find amount (last number with decimal or comma)
    amount = ''
    for f in reversed(fields):
        if re.match(r'^[0-9.,-]+$', f):
            amount = f.replace(',', '').replace(' ', '')
            break
    # Find ID number (13 digits)
    id_number = ''
    for f in fields:
        m = re.search(r'(\d{13})', f)
        if m:
            id_number = m.group(1)
            break
    # Return cleaned row
    return [account_id, name, date, '', amount] + ['']*9 + [id_number] + ['','']

def postprocess_csv(input_path, output_path):
    with open(input_path, encoding='utf-8') as fin, open(output_path, 'w', encoding='utf-8', newline='') as fout:
        reader = csv.reader(fin)
        writer = csv.writer(fout)
        header_rows = []
        data_rows = []
        for row in reader:
            if not any(row):
                continue
            if row[0] in ('Report_Header', 'Account_ID') or row[0].startswith('Run_Date') or row[0].startswith('Doctor'):
                header_rows.append(row)
            elif row[0] and (re.match(r'^[A-Z0-9]{6,}$', row[0]) or re.search(r'\d{6,}', row[0])):
                data_rows.append(clean_account_row(row))
        # Write headers
        for row in header_rows:
            writer.writerow(row)
        # Write column header if not present
        if not any('Account_ID' in r for r in header_rows):
            writer.writerow(['Account_ID','Account_Name','Last_Visit','Last_Receipt_Payment','Current','30_Days','60_Days','90_Days','120_Days','150_Days','Outstanding','Address','Status','Payment_Date','ID_Number','Claim_Number','Claim_Status'])
        # Write cleaned data
        for row in data_rows:
            writer.writerow(row)
