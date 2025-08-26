#!/usr/bin/env python3
"""
Debug script to investigate data filtering issues in the budget agent.
This will help identify why monthly data might be showing annual totals.
"""

import os
import sys
import duckdb
from datetime import datetime

# Add the parent directory to the path so we can import common
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from scripts.common import connect_db

def debug_monthly_data():
    """Debug the monthly data filtering"""
    con = connect_db()
    
    print("🔍 Debugging Monthly Data Filtering")
    print("=" * 50)
    
    # Check database schema
    schema = con.execute("DESCRIBE transactions").fetchdf()
    print("Database schema:")
    for _, row in schema.iterrows():
        print(f"  {row['column_name']}: {row['column_type']}")
    print()
    
    # Check date range in database
    date_range = con.execute("""
        SELECT 
            MIN(posted_at) as min_date,
            MAX(posted_at) as max_date,
            COUNT(*) as total_transactions
        FROM transactions
    """).fetchone()
    
    print(f"Database date range: {date_range[0]} to {date_range[1]}")
    print(f"Total transactions: {date_range[2]:,}")
    print()
    
    # Check data by year and month
    year_month_counts = con.execute("""
        SELECT 
            strftime('%Y', posted_at) as year,
            strftime('%m', posted_at) as month,
            COUNT(*) as count,
            SUM(CASE WHEN amount > 0 THEN amount ELSE 0 END) as income,
            SUM(CASE WHEN amount < 0 THEN amount ELSE 0 END) as expenses
        FROM transactions
        GROUP BY 1, 2
        ORDER BY 1, 2
    """).fetchdf()
    
    print("Transactions by year and month:")
    for _, row in year_month_counts.iterrows():
        print(f"  {row['year']}-{row['month']}: {row['count']:3d} transactions, "
              f"income: ${row['income']:8,.2f}, expenses: ${row['expenses']:8,.2f}")
    print()
    
    # Test the monthly filtering for August 2025
    test_month = "2025-08"
    print(f"Testing monthly filtering for {test_month}:")
    
    # Test old method (strftime)
    old_result = con.execute(f"""
        SELECT 
            COUNT(*) as count,
            SUM(CASE WHEN amount > 0 THEN amount ELSE 0 END) as income,
            SUM(CASE WHEN amount < 0 THEN amount ELSE 0 END) as expenses
        FROM transactions 
        WHERE strftime('%Y-%m', posted_at) = '{test_month}'
    """).fetchone()
    
    print(f"  Old method (strftime): {old_result[0]:,} transactions, "
          f"income: ${old_result[1]:,.2f}, expenses: ${old_result[2]:,.2f}")
    
    # Test new method (date bounds)
    try:
        year, month = test_month.split('-')
        year = int(year)
        month = int(month)
        
        start_date = f"{year:04d}-{month:02d}-01"
        if month == 12:
            end_date = f"{year + 1:04d}-01-01"
        else:
            end_date = f"{year:04d}-{month + 1:02d}-01"
        
        new_result = con.execute(f"""
            SELECT 
                COUNT(*) as count,
                SUM(CASE WHEN amount > 0 THEN amount ELSE 0 END) as income,
                SUM(CASE WHEN amount < 0 THEN amount ELSE 0 END) as expenses
            FROM transactions 
            WHERE posted_at >= '{start_date}' AND posted_at < '{end_date}'
        """).fetchone()
        
        print(f"  New method (date bounds): {new_result[0]:,} transactions, "
              f"income: ${new_result[1]:,.2f}, expenses: ${new_result[2]:,.2f}")
        
        # Show the actual dates in the result
        actual_dates = con.execute(f"""
            SELECT 
                MIN(posted_at) as min_date,
                MAX(posted_at) as max_date,
                COUNT(DISTINCT strftime('%Y', posted_at)) as unique_years,
                COUNT(DISTINCT strftime('%m', posted_at)) as unique_months
            FROM transactions 
            WHERE posted_at >= '{start_date}' AND posted_at < '{end_date}'
        """).fetchone()
        
        print(f"  Date range in result: {actual_dates[0]} to {actual_dates[1]}")
        print(f"  Unique years: {actual_dates[2]}, Unique months: {actual_dates[3]}")
        
    except Exception as e:
        print(f"  Error testing new method: {e}")
    
    print()
    
    # Show sample transactions for August 2025
    print(f"Sample transactions for {test_month}:")
    sample_txns = con.execute(f"""
        SELECT 
            posted_at, 
            merchant, 
            amount, 
            account,
            strftime('%Y-%m', posted_at) as year_month
        FROM transactions 
        WHERE strftime('%Y-%m', posted_at) = '{test_month}'
        ORDER BY posted_at DESC
        LIMIT 10
    """).fetchdf()
    
    if not sample_txns.empty:
        for _, row in sample_txns.iterrows():
            print(f"  {row['posted_at']} | {row['merchant']} | ${row['amount']:,.2f} | {row['account']} | {row['year_month']}")
    else:
        print("  No transactions found")
    
    con.close()

if __name__ == "__main__":
    debug_monthly_data()
