#!/usr/bin/env python3
"""
Simple CSV Data Validation Script for Medical Billing Bad Debt Report
This script analyzes the CSV file without external dependencies.
"""

import csv
import re
from datetime import datetime

def validate_csv_data(file_path):
    """Validate the CSV data and identify issues"""
    print("Loading CSV data...")
    
    with open(file_path, 'r', encoding='utf-8') as file:
        reader = csv.DictReader(file)
        rows = list(reader)
    
    print(f"Total records: {len(rows)}")
    print(f"Columns: {list(rows[0].keys()) if rows else 'No data'}")
    
    issues = []
    
    # 1. Check for missing critical values
    print("\n1. MISSING VALUES CHECK:")
    critical_fields = ['Account_ID', 'Patient_Name', 'Outstanding', 'Current_Amount']
    
    for field in critical_fields:
        missing_count = sum(1 for row in rows if not row.get(field, '').strip())
        if missing_count > 0:
            print(f"   {field}: {missing_count} missing values")
            issues.append(f"Missing values in {field}: {missing_count}")
        else:
            print(f"   {field}: ✓ No missing values")
    
    # 2. Check date format consistency
    print("\n2. DATE FORMAT VALIDATION:")
    date_pattern = r'^\d{2}\.\d{2}\.\d{2}$'
    invalid_dates = []
    
    for i, row in enumerate(rows):
        date_val = row.get('Last_Visit', '').strip()
        if date_val and not re.match(date_pattern, date_val):
            invalid_dates.append((i+2, date_val))  # +2 for header row and 0-based index
    
    if invalid_dates:
        print(f"   Found {len(invalid_dates)} invalid date formats:")
        for row_num, date_val in invalid_dates[:5]:  # Show first 5
            print(f"      Row {row_num}: '{date_val}'")
        issues.append(f"Invalid date formats: {len(invalid_dates)}")
    else:
        print("   ✓ All dates follow DD.MM.YY format")
    
    # 3. Check numeric values
    print("\n3. NUMERIC DATA VALIDATION:")
    numeric_fields = ['Current_Amount', '30_Days', '60_Days', '90_Days', '120_Days', '150_Days', 'Outstanding']
    
    for field in numeric_fields:
        non_numeric = []
        for i, row in enumerate(rows):
            value = row.get(field, '').strip()
            if value:
                try:
                    float(value)
                except ValueError:
                    non_numeric.append((i+2, value))
        
        if non_numeric:
            print(f"   {field}: {len(non_numeric)} non-numeric values")
            for row_num, value in non_numeric[:3]:
                print(f"      Row {row_num}: '{value}'")
            issues.append(f"Non-numeric values in {field}: {len(non_numeric)}")
        else:
            print(f"   {field}: ✓ All numeric")
    
    # 4. Check aging bucket logic
    print("\n4. AGING BUCKET VALIDATION:")
    aging_mismatches = []
    
    for i, row in enumerate(rows):
        try:
            aging_sum = (float(row.get('30_Days', 0)) + 
                        float(row.get('60_Days', 0)) + 
                        float(row.get('90_Days', 0)) + 
                        float(row.get('120_Days', 0)) + 
                        float(row.get('150_Days', 0)))
            outstanding = float(row.get('Outstanding', 0))
            
            if abs(aging_sum - outstanding) > 0.01:  # Allow for small rounding differences
                aging_mismatches.append((i+2, aging_sum, outstanding))
        except (ValueError, TypeError):
            continue
    
    if aging_mismatches:
        print(f"   Found {len(aging_mismatches)} records where aging buckets don't sum to Outstanding:")
        for row_num, calculated, outstanding in aging_mismatches[:5]:
            print(f"      Row {row_num}: Calculated={calculated:.2f}, Outstanding={outstanding:.2f}")
        issues.append(f"Aging bucket mismatches: {len(aging_mismatches)}")
    else:
        print("   ✓ All aging buckets sum correctly")
    
    # 5. Check for negative values
    print("\n5. NEGATIVE VALUE ANALYSIS:")
    negative_current = []
    
    for i, row in enumerate(rows):
        try:
            current_amount = float(row.get('Current_Amount', 0))
            if current_amount < 0:
                negative_current.append((i+2, row.get('Patient_Name', ''), current_amount))
        except (ValueError, TypeError):
            continue
    
    if negative_current:
        print(f"   Found {len(negative_current)} records with negative Current_Amount:")
        for row_num, patient_name, amount in negative_current[:5]:
            print(f"      Row {row_num}: {patient_name} - {amount:.2f}")
        print("   Note: Negative amounts may indicate credits or adjustments")
    else:
        print("   ✓ No negative current amounts")
    
    # 6. Check ID number format (South African ID pattern)
    print("\n6. ID NUMBER VALIDATION:")
    sa_id_pattern = r'^\d{13}$'
    invalid_ids = []
    
    for i, row in enumerate(rows):
        id_num = row.get('ID_Number', '').strip()
        if id_num and not re.match(sa_id_pattern, id_num):
            invalid_ids.append((i+2, id_num))
    
    if invalid_ids:
        print(f"   Found {len(invalid_ids)} invalid ID number formats:")
        for row_num, id_num in invalid_ids[:5]:
            print(f"      Row {row_num}: '{id_num}'")
        issues.append(f"Invalid ID formats: {len(invalid_ids)}")
    else:
        print("   ✓ All ID numbers follow 13-digit format (where provided)")
    
    # 7. Check for duplicate accounts
    print("\n7. DUPLICATE ANALYSIS:")
    account_ids = {}
    for i, row in enumerate(rows):
        account_id = row.get('Account_ID', '').strip()
        if account_id:
            if account_id in account_ids:
                account_ids[account_id].append(i+2)
            else:
                account_ids[account_id] = [i+2]
    
    duplicates = {k: v for k, v in account_ids.items() if len(v) > 1}
    if duplicates:
        print(f"   Found {len(duplicates)} duplicate Account_IDs:")
        for account_id, row_nums in list(duplicates.items())[:5]:
            print(f"      {account_id}: rows {row_nums}")
        issues.append(f"Duplicate Account_IDs: {len(duplicates)}")
    else:
        print("   ✓ All Account_IDs are unique")
    
    # 8. Summary statistics
    print("\n8. SUMMARY STATISTICS:")
    outstanding_amounts = []
    for row in rows:
        try:
            amount = float(row.get('Outstanding', 0))
            outstanding_amounts.append(amount)
        except (ValueError, TypeError):
            continue
    
    if outstanding_amounts:
        total = sum(outstanding_amounts)
        average = total / len(outstanding_amounts)
        outstanding_amounts.sort()
        median = outstanding_amounts[len(outstanding_amounts)//2]
        
        print(f"   Total Outstanding Amount: R{total:,.2f}")
        print(f"   Average Outstanding: R{average:,.2f}")
        print(f"   Median Outstanding: R{median:,.2f}")
        print(f"   Min Outstanding: R{min(outstanding_amounts):,.2f}")
        print(f"   Max Outstanding: R{max(outstanding_amounts):,.2f}")
    
    # 9. Issues summary
    if issues:
        print(f"\n9. ISSUES SUMMARY:")
        print(f"   Total issues found: {len(issues)}")
        for issue in issues:
            print(f"   - {issue}")
        
        print(f"\n10. RECOMMENDATIONS:")
        print("   - Review negative amounts for accuracy")
        print("   - Verify aging bucket calculations")
        print("   - Standardize ID number formats")
        print("   - Check for duplicate entries")
    else:
        print("\n9. DATA QUALITY:")
        print("   ✓ No major data quality issues found!")
    
    return len(issues)

if __name__ == "__main__":
    file_path = r"templates\attendance\medical_billing_bad_debt.csv"
    try:
        issue_count = validate_csv_data(file_path)
        print(f"\nValidation complete. Found {issue_count} issue types.")
    except FileNotFoundError:
        print(f"Error: Could not find file {file_path}")
    except Exception as e:
        print(f"Error during validation: {e}")
