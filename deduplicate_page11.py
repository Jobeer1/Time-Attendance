import pandas as pd

def deduplicate_page11():
    df = pd.read_csv('page11.csv')
    before = len(df)
    # Remove duplicates where both Account_ID and ID_Number are the same
    df = df.drop_duplicates(subset=['Account_ID', 'ID_Number'], keep='first')
    after = len(df)
    df.to_csv('page11.csv', index=False)
    print(f"Deduplicated page11.csv: {before} -> {after} rows")

if __name__ == "__main__":
    deduplicate_page11()
