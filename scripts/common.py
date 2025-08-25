import os, re, hashlib, datetime as dt
import pandas as pd
import duckdb
import yaml

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "db", "ledger.duckdb")
CONFIG_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "config")

def connect_db():
    con = duckdb.connect(DB_PATH)
    ensure_schema(con)
    return con

def ensure_schema(con):
    con.execute(
        """
        CREATE TABLE IF NOT EXISTS transactions (
            txn_id TEXT PRIMARY KEY,
            posted_at TIMESTAMP,
            description_raw TEXT,
            merchant TEXT,
            amount DOUBLE,
            currency TEXT,
            account TEXT,
            method TEXT,
            balance DOUBLE,
            reference TEXT,
            category TEXT,
            subcategory TEXT,
            fixed BOOLEAN,
            recurring BOOLEAN,
            internal_transfer BOOLEAN,
            source TEXT,
            imported_at TIMESTAMP
        )
        """
    )
    
    # Add recurring column if it doesn't exist (for existing databases)
    try:
        con.execute("ALTER TABLE transactions ADD COLUMN recurring BOOLEAN")
    except:
        pass  # Column already exists
    
    # Add internal_transfer column if it doesn't exist (for existing databases)
    try:
        con.execute("ALTER TABLE transactions ADD COLUMN internal_transfer BOOLEAN")
    except:
        pass  # Column already exists

def load_yaml(name):
    with open(os.path.join(CONFIG_DIR, name), "r") as f:
        return yaml.safe_load(f)

def fingerprint_txn(account, posted_at, amount, description):
    key = f"{account}|{posted_at}|{amount}|{description}"
    return hashlib.sha1(key.encode("utf-8")).hexdigest()

def guess_column(df, candidates):
    for c in candidates:
        if c in df.columns:
            return c
        # try case-insensitive
        for col in df.columns:
            if col.lower() == c.lower():
                return col
    return None

def clean_merchant(text):
    if not isinstance(text, str):
        return ""
    t = re.sub(r"\s+", " ", text.strip())
    # remove trailing codes like AU, card tails, numbers-only tokens
    t = re.sub(r"\bAU\b", "", t, flags=re.I)
    t = re.sub(r"\*+\d{2,}$", "", t)
    return t.strip()

def apply_rules(merchant, rules):
    for rule in rules:
        pat = rule.get("match")
        if pat and re.search(pat, merchant or "", flags=re.I):
            return rule["category"], rule.get("subcategory"), bool(rule.get("fixed", False))
    return None, None, None
