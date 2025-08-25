# Budget Agent (Local-First)

A small, config-driven budgeting tool that ingests CSV exports from your bank and card accounts, normalises and categorises transactions, stores them in DuckDB, detects recurring expenses, and produces a monthly Markdown report and a simple Streamlit dashboard.

## Quick start

```bash
# 1) Create and activate a virtual environment
python -m venv .venv
source .venv/bin/activate

# 2) Install dependencies
pip install -r requirements.txt

# 3) Populate raw CSVs into data/raw/<source>/
#    e.g., data/raw/ubank/2025-08-ubank.csv, data/raw/qantas/2025-08-qantas.csv

# 4) Run the pipeline (ingest + normalise + categorise + recurring + DB load)
python scripts/run_pipeline.py

# 5) Generate a monthly report (replace YYYY-MM)
python scripts/report_monthly.py --month 2025-08

# 6) Launch the dashboard
streamlit run app/dashboard.py
```

## Config

- `config/merchants.yaml`: regex-based merchant rules → category/subcategory/fixed
- `config/categories.yaml`: accepted category/subcategory definitions
- `config/budgets.yaml`: optional monthly budgets per category
- `config/sources.yaml`: simple column mapping hints per source

## Data model (DuckDB)
Table `transactions`:
```
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
source TEXT,
imported_at TIMESTAMP
```
