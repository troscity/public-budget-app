import os, glob, re, sys
import pandas as pd
from datetime import datetime as dt
from scripts.common import connect_db, load_yaml, fingerprint_txn, guess_column, clean_merchant, apply_rules

ROOT = os.path.dirname(os.path.dirname(__file__))
RAW_DIR = os.path.join(ROOT, "data", "raw")
PROCESSED_DIR = os.path.join(ROOT, "data", "processed")

def is_internal_transfer(merchant, description_raw, amount):
    """
    Identify internal transfers that should be excluded from spending calculations.
    These are movements between your own accounts, not actual income/expenses.
    """
    merchant_lower = merchant.lower()
    desc_lower = description_raw.lower()
    
    # Common internal transfer patterns
    transfer_keywords = [
        'internal transfer', 'transfer', 'withdrawal', 'deposit',
        'internal', 'opening deposit', 'funds transfer'
    ]
    
    # Check if merchant or description contains transfer keywords
    is_transfer = any(keyword in merchant_lower or keyword in desc_lower 
                     for keyword in transfer_keywords)
    
    # Additional checks for large round numbers that are likely transfers
    is_large_round = abs(amount) >= 500 and amount % 100 == 0
    
    # Exclude legitimate expenses that might match (like rent)
    is_legitimate = any(keyword in merchant_lower for keyword in ['rent', 'bpay', 'bill'])
    
    return is_transfer and is_large_round and not is_legitimate

def parse_csv(path, source_cfg):
    df = pd.read_csv(path)
    
    # Date column
    date_col = guess_column(df, source_cfg.get("date_cols", []))
    if date_col is None:
        raise ValueError(f"No date column found. Available columns: {list(df.columns)}. Expected: {source_cfg.get('date_cols', [])}")
    
    # Description column
    desc_col = guess_column(df, source_cfg.get("desc_cols", []))
    if desc_col is None:
        raise ValueError(f"No description column found. Available columns: {list(df.columns)}. Expected: {source_cfg.get('desc_cols', [])}")
    
    # Amount column
    amount_col = guess_column(df, source_cfg.get("amount_cols", []))
    if amount_col is None:
        raise ValueError(f"No amount column found. Available columns: {list(df.columns)}. Expected: {source_cfg.get('amount_cols', [])}")
    
    # Check if we have both Debit and Credit columns - if so, use credit/debit logic
    credit_col = guess_column(df, ["Credit", "credit"])
    debit_col = guess_column(df, ["Debit", "debit"])
    
    if credit_col and debit_col:
        # Handle currency formatting (remove $ and commas) before converting to numeric
        credit_raw = df[credit_col].astype(str).str.replace('$', '').str.replace(',', '')
        debit_raw = df[debit_col].astype(str).str.replace('$', '').str.replace(',', '')
        
        credit = pd.to_numeric(credit_raw, errors="coerce").fillna(0)
        debit = pd.to_numeric(debit_raw, errors="coerce").fillna(0)
        amount = credit - debit
    elif amount_col in df.columns:
        # Single amount column
        amount = pd.to_numeric(df[amount_col], errors="coerce")
    elif credit_col:
        amount = pd.to_numeric(df[credit_col], errors="coerce")
    elif debit_col:
        amount = -pd.to_numeric(df[debit_col], errors="coerce")
    else:
        raise ValueError(f"Could not determine amount from columns: {list(df.columns)}")

    if source_cfg.get("debit_negative", True):
        pass  # already handled by credit-debit. If only Amount provided, assume negative for debits in CSV.

    # Balance (optional)
    bal_col = guess_column(df, source_cfg.get("balance_cols", []))
    balance = pd.to_numeric(df.get(bal_col, pd.Series([None]*len(df))), errors="coerce") if bal_col else None

    # Coerce dates
    if source_cfg.get("source") == "ubank" or "ubank" in path.lower():
        # Handle ubank's specific format: "13:26 25-08-25" (time first, then DD-MM-YY)
        posted_at = pd.to_datetime(df[date_col], format="%H:%M %d-%m-%y", errors="coerce")
    else:
        posted_at = pd.to_datetime(df[date_col], errors="coerce")
    
    # If parsing failed, try alternative formats
    if posted_at.isna().all():
        posted_at = pd.to_datetime(df[date_col], errors="coerce")
    
    description_raw = df[desc_col].astype(str)
    
    # Build canonical frame
    out = pd.DataFrame({
        "posted_at": posted_at,
        "description_raw": description_raw,
        "merchant": description_raw.map(clean_merchant),
        "amount": amount.astype(float),
        "currency": source_cfg.get("currency", "AUD"),
        "account": source_cfg.get("account", "Unknown"),
        "method": "",
        "balance": balance if balance is not None else None,
        "reference": "",
        "source": os.path.basename(os.path.dirname(path)),
    })
    
    # Identify internal transfers
    out["internal_transfer"] = out.apply(
        lambda row: is_internal_transfer(row["merchant"], row["description_raw"], row["amount"]), 
        axis=1
    )
    
    # drop rows with no date or amount
    out = out.dropna(subset=["posted_at"])
    out = out[out["amount"].notna()]
    return out

def dedupe(con, df):
    # We use a SHA1 fingerprint and ignore rows already present
    df = df.copy()
    df["txn_id"] = [
        fingerprint_txn(r["account"], r["posted_at"], r["amount"], r["description_raw"])
        for _, r in df.iterrows()
    ]
    
    # Check for duplicates within the current batch
    duplicate_ids = df[df.duplicated(subset=["txn_id"], keep=False)]
    if not duplicate_ids.empty:
        print(f"Warning: Found {len(duplicate_ids)} duplicate transactions within the current file")
        df = df.drop_duplicates(subset=["txn_id"], keep="first")
    
    # Query existing txn_ids
    existing = set(con.execute("SELECT txn_id FROM transactions").fetchdf()["txn_id"].tolist())
    df = df[~df["txn_id"].isin(existing)]
    return df

def categorise(df, rules):
    cats, subs, fixeds = [], [], []
    for m in df["merchant"].tolist():
        c, s, f = apply_rules(m, rules)
        cats.append(c)
        subs.append(s)
        fixeds.append(f)
    df["category"] = cats
    df["subcategory"] = subs
    df["fixed"] = [bool(x) if x is not None else None for x in fixeds]
    return df

def detect_recurring(con):
    """
    Detect recurring transactions by identifying merchants that appear in 
    at least 2 different months within the last 3 months.
    """
    q = """
    WITH recent AS (
        SELECT
            merchant,
            date_trunc('month', posted_at) AS m,
            COUNT(*) AS n,
            AVG(ABS(amount)) AS avg_amt
        FROM transactions
        WHERE posted_at >= current_timestamp - INTERVAL 3 MONTH
        GROUP BY 1,2
    ),
    agg AS (
        SELECT merchant, COUNT(DISTINCT m) AS month_hits
        FROM recent
        GROUP BY merchant
    )
    UPDATE transactions AS t
    SET recurring = true
    FROM agg AS a
    WHERE t.merchant = a.merchant AND a.month_hits >= 2;
    """
    con.execute(q)


def main():
    from scripts.common import connect_db  # local import so file can be created without duckdb installed
    con = connect_db()
    cfg = load_yaml("sources.yaml")["sources"]
    rules = load_yaml("merchants.yaml")["rules"]

    sources = [d for d in os.listdir(RAW_DIR) if os.path.isdir(os.path.join(RAW_DIR, d))]
    total_new = 0
    for src in sources:
        src_dir = os.path.join(RAW_DIR, src)
        files = glob.glob(os.path.join(src_dir, "*.csv"))
        if not files:
            continue
        source_cfg = cfg.get(src, {})
        for fpath in files:
            try:
                df = parse_csv(fpath, source_cfg)
                if df.empty:
                    continue
                
                df = categorise(df, rules)
                df = dedupe(con, df)
                if df.empty:
                    # move file to processed regardless to prevent re-reading
                    dest = os.path.join(PROCESSED_DIR, os.path.basename(src_dir) + "-" + os.path.basename(fpath))
                    os.replace(fpath, dest)
                    continue
                
                df["imported_at"] = pd.Timestamp.now(tz="UTC")
                # Fill defaults
                for col in ["category","subcategory","fixed"]:
                    if col not in df.columns: df[col] = None
                df["recurring"] = None
                # Write to DB
                con.register("df", df)
                con.execute("""
                    INSERT INTO transactions
                    SELECT
                        txn_id, posted_at, description_raw, merchant, amount, currency,
                        account, method, balance, reference, category, subcategory,
                        fixed, recurring, source, imported_at, internal_transfer
                    FROM df
                """)
                total_new += len(df)
                # move processed file
                dest = os.path.join(PROCESSED_DIR, os.path.basename(src_dir) + "-" + os.path.basename(fpath))
                os.replace(fpath, dest)
            except Exception as e:
                print(f"Error processing {fpath}: {e}")
                import traceback
                traceback.print_exc()
                continue

    # recurring detector
    detect_recurring(con)
    print(f"Ingest complete. New records: {total_new}")

if __name__ == "__main__":
    main()
