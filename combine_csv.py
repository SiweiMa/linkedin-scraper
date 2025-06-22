#!/usr/bin/env python3
"""
Script to combine all LinkedIn CSV files into one consolidated file.
"""

import pandas as pd
import glob
import os

def combine_csv_files():
    """
    Combine all linkedin_data_*.csv files into one consolidated CSV file.
    """
    # Find all CSV files matching the pattern
    csv_files = glob.glob('linkedin_data_*.csv')
    csv_files.sort()  # Sort to ensure consistent order
    
    print(f"Found {len(csv_files)} CSV files to combine:")
    for file in csv_files:
        print(f"  - {file}")
    
    # Read and combine all CSV files
    combined_data = []
    
    for file in csv_files:
        try:
            # Read CSV file
            df = pd.read_csv(file)
            
            # Skip if file is empty (only header)
            if len(df) == 0:
                print(f"  Skipping {file} - no data rows")
                continue
            
            combined_data.append(df)
            print(f"  Added {len(df)} rows from {file}")
            
        except Exception as e:
            print(f"  Error reading {file}: {e}")
    
    if not combined_data:
        print("No data found to combine!")
        return
    
    # Combine all dataframes
    final_df = pd.concat(combined_data, ignore_index=True)
    
    # Remove any duplicate rows based on all columns
    initial_rows = len(final_df)
    final_df = final_df.drop_duplicates()
    final_rows = len(final_df)
    
    if initial_rows != final_rows:
        print(f"Removed {initial_rows - final_rows} duplicate rows")
    
    # Save combined data
    output_file = 'linkedin_data_combined.csv'
    final_df.to_csv(output_file, index=False)
    
    print(f"\nCombined {len(csv_files)} files into {output_file}")
    print(f"Total rows: {len(final_df)}")
    print(f"Columns: {list(final_df.columns)}")
    
    # Show sample of combined data
    print("\nFirst 5 rows of combined data:")
    print(final_df.head().to_string())
    
    return output_file

if __name__ == "__main__":
    combine_csv_files() 