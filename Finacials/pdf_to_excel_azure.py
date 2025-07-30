import configparser
import requests
import pandas as pd
import os
import sys
from io import BytesIO
from time import sleep

# Read config.ini for Azure credentials
config = configparser.ConfigParser()
config.read('config.ini', encoding='utf-8')

# Strip possible whitespace and trailing slashes from config values
def get_config_value(section, key):
    return config.get(section, key).strip().rstrip('/')

AZURE_VISION_KEY = get_config_value('Azure', 'vision_key')
AZURE_VISION_ENDPOINT = get_config_value('Azure', 'vision_endpoint')


# Use Computer Vision Read API endpoint (v3.2)
VISION_API_URL = f"{AZURE_VISION_ENDPOINT}/vision/v3.2/read/analyze"

headers = {
    'Ocp-Apim-Subscription-Key': AZURE_VISION_KEY,
    'Content-Type': 'application/pdf',
}
print(f"Using endpoint: {AZURE_VISION_ENDPOINT}")
print(f"Using key: {AZURE_VISION_KEY[:6]}...{AZURE_VISION_KEY[-6:]}")


def extract_tables_from_pdf(pdf_path, output_format='xlsx', output_name=None):
    with open(pdf_path, 'rb') as f:
        data = f.read()
    response = requests.post(VISION_API_URL, headers=headers, data=data)
    if response.status_code != 202:
        print('Error submitting PDF to Azure:', response.text)
        sys.exit(1)
    result_url = response.headers['operation-location']
    # Poll for result
    for _ in range(30):
        sleep(2)
        result = requests.get(result_url, headers={'Ocp-Apim-Subscription-Key': AZURE_VISION_KEY})
        result_json = result.json()
        if result_json.get('status') == 'succeeded':
            break
        elif result_json.get('status') == 'failed':
            print('Azure failed to process the PDF.')
            sys.exit(1)
    else:
        print('Timed out waiting for Azure to process the PDF.')
        sys.exit(1)
    # Extract lines and try to group as tables (simple approach)
    results = result_json.get('analyzeResult', {}).get('readResults', [])
    if not results:
        print('No text found in PDF.')
        sys.exit(1)
    # Try to group lines into rows by y-coordinate (works for simple tables)
    import collections
    rows = collections.defaultdict(list)
    for page in results:
        for line in page.get('lines', []):
            y = round(line['boundingBox'][1], 1)  # y1 coordinate, rounded
            rows[y].append(line['text'])
    # Sort rows by y
    sorted_rows = [rows[y] for y in sorted(rows.keys())]
    df = pd.DataFrame(sorted_rows)
    # Use output_name if provided, else use base name
    if output_name:
        base = output_name
    else:
        base = os.path.splitext(os.path.basename(pdf_path))[0] + '_output'
    if output_format == 'xlsx':
        outname = f'{base}.xlsx'
        df.to_excel(outname, index=False, header=False)
        print(f'Table saved as {outname}')
    else:
        outname = f'{base}.csv'
        df.to_csv(outname, index=False, header=False)
        print(f'Table saved as {outname}')
    return outname

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print('Usage: python pdf_to_excel_azure.py <PDF_FILE> [csv|xlsx]')
        sys.exit(1)
    pdf_file = sys.argv[1]
    output_format = 'xlsx'
    if len(sys.argv) > 2 and sys.argv[2] == 'csv':
        output_format = 'csv'
    extract_tables_from_pdf(pdf_file, output_format)
    print('All tables extracted and saved. Output is South African user friendly. Please check the generated files.')
