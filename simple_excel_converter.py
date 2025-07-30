import pandas as pd
import os

def simple_csv_to_excel():
    try:
        # File paths
        csv_file = r"c:\Users\Admin\Desktop\ELC\Workspaces\Time Attendance\reports1.csv"
        excel_file = r"c:\Users\Admin\Desktop\ELC\Workspaces\Time Attendance\reports1.xlsx"
        
        print(f"Reading CSV file: {csv_file}")
        
        # Read the CSV file
        df = pd.read_csv(csv_file)
        print(f"CSV loaded successfully with {len(df)} rows")
        
        # Create Excel writer with formatting
        with pd.ExcelWriter(excel_file, engine='openpyxl') as writer:
            # Write report header info (first 6 rows)
            header_df = df.iloc[:6]
            header_df.to_excel(writer, sheet_name='Report Info', index=False, header=False)
            
            # Write main data (skip first 7 rows which include header info and blank row)
            data_df = df.iloc[7:]
            data_df.to_excel(writer, sheet_name='Patient Data', index=False)
            
            # Access the workbook and worksheet for formatting
            workbook = writer.book
            
            # Format Report Info sheet
            info_sheet = writer.sheets['Report Info']
            info_sheet.column_dimensions['A'].width = 25
            info_sheet.column_dimensions['B'].width = 40
            
            # Format Patient Data sheet
            data_sheet = writer.sheets['Patient Data']
            
            # Auto-adjust column widths
            for column in data_sheet.columns:
                max_length = 0
                column_letter = column[0].column_letter
                
                for cell in column:
                    try:
                        if len(str(cell.value)) > max_length:
                            max_length = len(str(cell.value))
                    except:
                        pass
                
                adjusted_width = min(max_length + 2, 50)
                data_sheet.column_dimensions[column_letter].width = adjusted_width
        
        print(f"Excel file created successfully: {excel_file}")
        return True
        
    except Exception as e:
        print(f"Error: {str(e)}")
        return False

if __name__ == "__main__":
    success = simple_csv_to_excel()
    if success:
        print("Conversion completed successfully!")
    else:
        print("Conversion failed!")
