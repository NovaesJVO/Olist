#!/usr/bin/env python3
"""
Date Shift Script for Olist Dataset

Applies a fixed offset of 2556 days to timestamp columns,
shifting dates from 2016-2018 to 2023-2025.

Usage:
    python date_shift_olist.py --input-dir ./dados_originais --output-dir ./dados_ajustados

Output:
    - dados_ajustados/ with all 9 CSVs (3 with shifted timestamps)
    - Validation report showing duration preservation
"""

import argparse
import sys
from pathlib import Path
from datetime import timedelta
import pandas as pd


# Mapping of files to timestamp columns
TIMESTAMP_COLS = {
    'olist_orders_dataset.csv': [
        'order_purchase_timestamp',
        'order_approved_at',
        'order_delivered_carrier_date',
        'order_delivered_customer_date',
        'order_estimated_delivery_date'
    ],
    'olist_order_items_dataset.csv': [
        'shipping_limit_date'
    ],
    'olist_order_reviews_dataset.csv': [
        'review_creation_date',
        'review_answer_timestamp'
    ]
}

OFFSET_DAYS = 2556


def shift_dates(input_dir, output_dir, offset_days=OFFSET_DAYS):
    """
    Apply fixed date offset to timestamp columns.
    
    Args:
        input_dir (str): Path to dados_originais/
        output_dir (str): Path to dados_ajustados/
        offset_days (int): Days to add to timestamps
    
    Returns:
        dict: Validation results
    """
    
    input_path = Path(input_dir)
    output_path = Path(output_dir)
    
    # Create output directory
    output_path.mkdir(exist_ok=True, parents=True)
    
    offset = timedelta(days=offset_days)
    validation_results = {}
    
    print(f"📁 Input:  {input_path}")
    print(f"📁 Output: {output_path}")
    print(f"⏳ Offset: {offset_days} days\n")
    
    # Process all CSV files
    csv_files = sorted(input_path.glob('*.csv'))
    
    if not csv_files:
        print(f"❌ No CSV files found in {input_path}")
        return None
    
    for csv_file in csv_files:
        filename = csv_file.name
        output_file = output_path / filename
        
        print(f"Processing: {filename}")
        
        # Read CSV
        try:
            df = pd.read_csv(csv_file)
        except Exception as e:
            print(f"  ❌ Error reading file: {e}")
            return None
        
        # Check if this file has timestamp columns
        if filename not in TIMESTAMP_COLS:
            # Copy file as-is
            df.to_csv(output_file, index=False)
            print(f"  ✓ Copied (no timestamps)")
            continue
        
        # Shift timestamps
        cols_to_shift = TIMESTAMP_COLS[filename]
        df_before = df.copy()  # Keep copy for validation
        
        for col in cols_to_shift:
            if col in df.columns:
                # Convert to datetime and apply offset
                df[col] = pd.to_datetime(df[col], errors='coerce') + offset
        
        # Validate duration preservation
        validation = validate_durations(filename, df_before, df)
        validation_results[filename] = validation
        
        # Save shifted file
        df.to_csv(output_file, index=False)
        
        shifted_count = len(cols_to_shift)
        print(f"  ✓ Shifted {shifted_count} columns")
        
        # Show sample dates
        for col in cols_to_shift:
            if col in df.columns and df[col].notna().any():
                sample_before = df_before[col].dropna().iloc[0] if df_before[col].notna().any() else None
                sample_after = df[col].dropna().iloc[0] if df[col].notna().any() else None
                print(f"    {col}:")
                print(f"      Before: {sample_before}")
                print(f"      After:  {sample_after}")
    
    return validation_results


def validate_durations(filename, df_before, df_after):
    """
    Validate that durations between dates are preserved.
    
    Args:
        filename (str): File being validated
        df_before (pd.DataFrame): Original dataframe
        df_after (pd.DataFrame): Shifted dataframe
    
    Returns:
        dict: Validation result
    """
    
    # Define duration pairs to validate
    duration_pairs = {
        'olist_orders_dataset.csv': [
            ('order_purchase_timestamp', 'order_delivered_customer_date'),
            ('order_purchase_timestamp', 'order_estimated_delivery_date'),
        ],
        'olist_order_reviews_dataset.csv': [
            ('review_creation_date', 'review_answer_timestamp'),
        ]
    }
    
    result = {'status': 'PASS', 'details': []}
    
    if filename not in duration_pairs:
        return result
    
    pairs = duration_pairs[filename]
    
    for col1, col2 in pairs:
        if col1 not in df_before.columns or col2 not in df_before.columns:
            continue
        
        # Calculate durations
        dur_before = pd.to_datetime(df_before[col2], errors='coerce') - \
                     pd.to_datetime(df_before[col1], errors='coerce')
        dur_after = pd.to_datetime(df_after[col2], errors='coerce') - \
                    pd.to_datetime(df_after[col1], errors='coerce')
        
        # Compare (ignoring NaNs)
        mask = dur_before.notna() & dur_after.notna()
        if mask.any():
            diff = (dur_after[mask] - dur_before[mask]).abs()
            max_diff = diff.max()
            
            # Duration should be identical (0 difference)
            if max_diff == pd.Timedelta(0):
                detail = f"✓ {col1} → {col2}: Diff = 0.00s"
            else:
                detail = f"✗ {col1} → {col2}: Max Diff = {max_diff}"
                result['status'] = 'FAIL'
            
            result['details'].append(detail)
    
    return result


def main():
    parser = argparse.ArgumentParser(
        description='Shift dates in Olist dataset by fixed offset'
    )
    parser.add_argument(
        '--input-dir',
        default='./dados_originais',
        help='Path to input directory (default: ./dados_originais)'
    )
    parser.add_argument(
        '--output-dir',
        default='./dados_ajustados',
        help='Path to output directory (default: ./dados_ajustados)'
    )
    parser.add_argument(
        '--offset-days',
        type=int,
        default=OFFSET_DAYS,
        help=f'Days to offset (default: {OFFSET_DAYS})'
    )
    
    args = parser.parse_args()
    
    # Execute shift
    results = shift_dates(args.input_dir, args.output_dir, args.offset_days)
    
    if results is None:
        sys.exit(1)
    
    # Print validation summary
    print("\n" + "="*60)
    print("VALIDATION SUMMARY")
    print("="*60)
    
    for filename, validation in results.items():
        if validation['details']:
            print(f"\n{filename}:")
            for detail in validation['details']:
                print(f"  {detail}")
    
    # Overall status
    all_pass = all(v['status'] == 'PASS' for v in results.values() if v['details'])
    
    print("\n" + "="*60)
    if all_pass:
        print("✅ All validations PASSED")
    else:
        print("⚠️  Some validations may have issues")
    print("="*60 + "\n")
    
    print(f"📊 Output directory: {Path(args.output_dir).resolve()}")
    print(f"📝 Period shifted: ~2016-09 → ~2023-09, ~2018-10 → ~2025-10")


if __name__ == '__main__':
    main()
