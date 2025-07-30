#!/usr/bin/env python3
"""
Simple Excel Converter for Page 5 - JUN QUARTERLY WRITE OFFS
"""

import pandas as pd
from datetime import datetime
import os

def create_page5_excel_simple():
    """Convert page5.csv to Excel with basic formatting"""
    
    try:
        # Read the account data (skip header rows)
        df = pd.read_csv('page5.csv', skiprows=6)
        print(f"✓ Successfully read page5.csv with {len(df)} account records")
        
        # Convert numeric columns
        numeric_columns = ['Current', '30_Days', '60_Days', '90_Days', '120_Days', '150_Days', 'Outstanding', 'Last_Receipt_Payment']
        for col in numeric_columns:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
        
        # Create Excel file with summary
        with pd.ExcelWriter('page5_corrected.xlsx', engine='openpyxl') as writer:
            # Write main data
            df.to_excel(writer, sheet_name='Account Data', index=False)
            
            # Create summary data
            summary_data = {
                'Metric': [
                    'Total Accounts',
                    'Total Outstanding',
                    'Average Outstanding',
                    'Highest Outstanding',
                    'Accounts > R1000',
                    'Total Payments Received',
                    'Run Date',
                    'Doctor',
                    'Page Number'
                ],
                'Value': [
                    len(df),
                    f"R {df['Outstanding'].sum():,.2f}",
                    f"R {df['Outstanding'].mean():,.2f}",
                    f"R {df['Outstanding'].max():,.2f}",
                    len(df[df['Outstanding'] > 1000]),
                    f"R {abs(df[df['Last_Receipt_Payment'] < 0]['Last_Receipt_Payment'].sum()):,.2f}",
                    "26.06.25",
                    "DR. C.I. STOYANOV",
                    "5"
                ]
            }
            
            summary_df = pd.DataFrame(summary_data)
            summary_df.to_excel(writer, sheet_name='Summary', index=False)
            
            # Create aging analysis
            aging_data = {
                'Age Bucket': ['Current', '30 Days', '60 Days', '90 Days', '120 Days', '150+ Days'],
                'Amount': [
                    df['Current'].sum(),
                    df['30_Days'].sum(),
                    df['60_Days'].sum(),
                    df['90_Days'].sum(),
                    df['120_Days'].sum(),
                    df['150_Days'].sum()
                ]
            }
            
            aging_df = pd.DataFrame(aging_data)
            aging_df['Percentage'] = (aging_df['Amount'] / df['Outstanding'].sum() * 100).round(2)
            aging_df.to_excel(writer, sheet_name='Aging Analysis', index=False)
        
        print(f"✓ Successfully created page5_corrected.xlsx")
        return True
        
    except Exception as e:
        print(f"✗ Error creating Excel file: {e}")
        return False

if __name__ == "__main__":
    print("Creating Page 5 Excel Report (Corrected)...")
    print("=" * 50)
    
    if create_page5_excel_simple():
        print("=" * 50)
        print("✓ Page 5 Excel conversion completed successfully!")
        print("✓ Created: page5_corrected.xlsx")
    else:
        print("✗ Failed to create Excel file")
