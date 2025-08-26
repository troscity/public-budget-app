#!/usr/bin/env python3
"""
Test script to verify internal transfer detection and refund identification.
Run this after processing your CSV files to see what transfers were detected.
"""

import os
import sys
import duckdb
from datetime import datetime, timedelta

# Add the parent directory to the path so we can import common
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from scripts.common import connect_db

def test_transfer_detection():
    """Test the internal transfer detection functionality"""
    con = connect_db()
    
    print("🔍 Testing Internal Transfer Detection")
    print("=" * 50)
    
    # Check if the database has the new columns
    schema = con.execute("DESCRIBE transactions").fetchdf()
    has_refund_col = 'is_refund' in schema['column_name'].values
    has_transfer_col = 'internal_transfer' in schema['column_name'].values
    
    print(f"Database has refund column: {has_refund_col}")
    print(f"Database has transfer column: {has_transfer_col}")
    print()
    
    if not has_transfer_col:
        print("❌ internal_transfer column not found. Run the pipeline first.")
        return
    
    # Get recent transactions
    recent_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
    
    # Show internal transfers
    transfers = con.execute("""
        SELECT 
            posted_at, 
            merchant, 
            amount, 
            account, 
            source,
            description_raw
        FROM transactions 
        WHERE internal_transfer = true 
        AND posted_at >= ?
        ORDER BY posted_at DESC
        LIMIT 20
    """, [recent_date]).fetchdf()
    
    if transfers.empty:
        print("✅ No internal transfers found in the last 30 days")
    else:
        print(f"🔄 Found {len(transfers)} internal transfers in the last 30 days:")
        print()
        for _, row in transfers.iterrows():
            print(f"  {row['posted_at']} | {row['account']} | {row['merchant']} | ${row['amount']:,.2f}")
            print(f"    Description: {row['description_raw']}")
            print()
    
    # Show potential transfer pairs
    print("🔗 Potential Transfer Pairs (equal/opposite amounts across accounts):")
    pairs = con.execute("""
        WITH potential_pairs AS (
            SELECT 
                t1.txn_id as t1_id,
                t2.txn_id as t2_id,
                t1.amount as t1_amount,
                t2.amount as t2_amount,
                t1.account as t1_account,
                t2.account as t2_account,
                t1.posted_at as t1_date,
                t2.posted_at as t2_date,
                ABS(t1.amount + t2.amount) as amount_diff,
                ABS(EXTRACT(EPOCH FROM (t1.posted_at - t2.posted_at))) / 86400 as days_diff
            FROM transactions t1
            JOIN transactions t2 ON (
                t1.txn_id != t2.txn_id
                AND t1.account != t2.account
                AND ABS(t1.amount + t2.amount) < 0.01
                AND ABS(EXTRACT(EPOCH FROM (t1.posted_at - t2.posted_at))) / 86400 <= 3
                AND (t1.internal_transfer IS NULL OR t1.internal_transfer = false)
                AND (t2.internal_transfer IS NULL OR t2.internal_transfer = false)
            )
            WHERE t1.amount > 0 AND t2.amount < 0
        )
        SELECT 
            t1_account, t2_account, t1_amount, t2_amount, days_diff
        FROM potential_pairs
        ORDER BY days_diff ASC
        LIMIT 10
    """).fetchdf()
    
    if pairs.empty:
        print("  No potential transfer pairs found")
    else:
        for _, pair in pairs.iterrows():
            print(f"  {pair['t1_account']} ${pair['t1_amount']:,.2f} ↔ {pair['t2_account']} ${pair['t2_amount']:,.2f} ({pair['days_diff']:.1f} days apart)")
    
    print()
    
    # Show refunds if the column exists
    if has_refund_col:
        print("💸 Refunds Identified:")
        refunds = con.execute("""
            SELECT 
                posted_at, 
                merchant, 
                amount, 
                account, 
                description_raw
            FROM transactions 
            WHERE is_refund = true 
            AND posted_at >= ?
            ORDER BY posted_at DESC
            LIMIT 10
        """, [recent_date]).fetchdf()
        
        if refunds.empty:
            print("  No refunds found in the last 30 days")
        else:
            for _, row in refunds.iterrows():
                print(f"  {row['posted_at']} | {row['account']} | {row['merchant']} | ${row['amount']:,.2f}")
                print(f"    Description: {row['description_raw']}")
                print()
    
    con.close()

if __name__ == "__main__":
    test_transfer_detection()
