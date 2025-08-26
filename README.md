# Budget Agent 🚀

A powerful, config-driven personal finance management system that automatically processes CSV exports from multiple bank and credit card accounts. Features intelligent transaction categorization, recurring expense detection, and beautiful monthly reports with an interactive dashboard.

## ✨ Features

- **🔄 Multi-Source CSV Processing**: Supports various bank formats (Ubank, Qantas, PayPal, Apple Pay)
- **🧠 Smart Categorization**: Regex-based merchant rules for automatic transaction categorization
- **💰 Recurring Expense Detection**: Automatically identifies recurring transactions
- **📊 Monthly Reports**: Generate beautiful Markdown reports with category breakdowns
- **🎯 Interactive Dashboard**: Streamlit-based dashboard for monthly spending analysis
- **🗄️ DuckDB Storage**: Fast, local database for transaction storage
- **⚙️ Configurable**: Easy-to-modify YAML configuration files
- **🚫 Internal Transfer Filtering**: Automatically excludes internal account transfers from spending calculations

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- Git

### Installation

```bash
# 1. Clone the repository
git clone https://github.com/troscity/budget-agent.git
cd budget-agent

# 2. Create and activate virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt
```

### First Run

```bash
# 1. Place your CSV files in data/raw/<source>/
#    Example structure:
#    data/raw/ubank/2025-08-ubank.csv
#    data/raw/qantas/2025-08-qantas.csv

# 2. Run the pipeline (processes CSVs, categorizes, stores in DB)
python -m scripts.run_pipeline

# 3. Generate monthly report
python -m scripts.report_monthly --month 2025-08

# 4. Launch interactive dashboard
streamlit run app/dashboard.py
```

## 📁 Project Structure

```
budget-agent/
├── app/                    # Application files
│   ├── dashboard.py       # Streamlit dashboard
│   └── agent.py           # Main agent logic
├── config/                 # Configuration files
│   ├── sources.yaml       # CSV column mapping per source
│   ├── merchants.yaml     # Merchant categorization rules
│   ├── categories.yaml    # Category definitions
│   └── budgets.yaml       # Monthly budget targets
├── data/                   # Data directory
│   ├── raw/               # Raw CSV files (not in git)
│   └── processed/         # Processed files (not in git)
├── db/                     # Database files (not in git)
├── reports/                # Generated reports (not in git)
├── scripts/                # Processing scripts
│   ├── run_pipeline.py    # Main CSV processing pipeline
│   ├── report_monthly.py  # Monthly report generator
│   └── common.py          # Shared utilities
├── systemd/                # Systemd service files
└── requirements.txt        # Python dependencies
```

## ⚙️ Configuration

### Sources Configuration (`config/sources.yaml`)
Defines how to parse different bank CSV formats:

```yaml
sources:
  ubank:
    date_cols: ["Date and time", "Date"]
    desc_cols: ["Description", "Details"]
    amount_cols: ["Amount", "Debit", "Credit"]
    currency: "AUD"
    account: "Ubank Spend"
    debit_negative: true
```

### Merchant Rules (`config/merchants.yaml`)
Regex-based rules for automatic categorization:

```yaml
rules:
  - match: "ALDI|COLES|WOOLWORTHS"
    category: "Groceries"
    subcategory: "Supermarket"
    fixed: false
  - match: "RENT|MORTGAGE"
    category: "Fixed"
    subcategory: "Housing"
    fixed: true
```

### Categories (`config/categories.yaml`)
Define your spending categories and subcategories:

```yaml
categories:
  Groceries:
    - Supermarket
    - Local Market
  Fixed:
    - Housing
    - Utilities
    - Insurance
```

## 🔄 Usage Workflow

### 1. Data Ingestion
```bash
# Process new CSV files
python -m scripts.run_pipeline
```

**What happens:**
- Parses CSV files from `data/raw/<source>/`
- Normalizes data to canonical schema
- Applies merchant categorization rules
- Detects recurring transactions
- Stores in DuckDB database
- Moves processed files to `data/processed/`

### 2. Generate Reports
```bash
# Generate monthly report
python -m scripts.report_monthly --month 2025-08
```

**Outputs:**
- `reports/2025-08/report.md` - Human-readable summary
- `reports/2025-08/by_category.csv` - Category breakdown
- `reports/2025-08/by_merchant.csv` - Merchant analysis

### 3. Interactive Dashboard
```bash
# Launch dashboard
streamlit run app/dashboard.py
```

**Features:**
- Monthly spending overview
- Category breakdown with charts
- Top merchants analysis
- Transaction filtering
- Monthly trends comparison

## 🗄️ Database Schema

The system uses DuckDB with the following schema:

```sql
CREATE TABLE transactions (
    txn_id TEXT PRIMARY KEY,           -- Unique transaction ID
    posted_at TIMESTAMP,               -- Transaction date/time
    description_raw TEXT,              -- Original description
    merchant TEXT,                     -- Cleaned merchant name
    amount DOUBLE,                     -- Transaction amount
    currency TEXT,                     -- Currency code
    account TEXT,                      -- Account name
    method TEXT,                       -- Payment method
    balance DOUBLE,                    -- Account balance
    reference TEXT,                    -- Reference number
    category TEXT,                     -- Spending category
    subcategory TEXT,                  -- Subcategory
    fixed BOOLEAN,                     -- Is this a fixed expense?
    recurring BOOLEAN,                 -- Is this recurring?
    internal_transfer BOOLEAN,         -- Is this an internal transfer?
    source TEXT,                       -- Data source (bank name)
    imported_at TIMESTAMP              -- When imported
);
```

## 🔧 Advanced Features

### Recurring Transaction Detection
Automatically identifies merchants that appear in multiple months:
- Minimum 2 months in last 3 months
- Updates `recurring` flag in database

### Internal Transfer Filtering
Smart detection of internal account movements:
- Identifies transfers between your own accounts
- Excludes from spending calculations
- Provides transparency in reports

### Duplicate Prevention
- SHA1 fingerprinting of transactions
- Prevents duplicate imports
- Handles CSV re-processing safely

## 📊 Sample Output

### Monthly Report
```markdown
# Monthly Report — 2025-08

**Income:** $23,794.47
**Expenses:** $-18,630.81
**Net:** $5,163.66

**Internal Transfers:** 10 transactions totaling $21,400.00

## Spend by Category
| category      |   total |
|:--------------|--------:|
| Fixed         | -9,298.97 |
| Groceries     | -487.64 |
| Eating Out    | -471.58 |
```

### Dashboard Metrics
- Monthly income/expenses overview
- Category breakdown with charts
- Top merchants analysis
- Transaction filtering and search

## 🚀 Deployment

### Local Development
```bash
# Run in development mode
streamlit run app/dashboard.py --server.port 8501
```

### Production (Systemd)
```bash
# Install systemd services
sudo cp systemd/*.service /etc/systemd/system/
sudo cp systemd/*.timer /etc/systemd/system/

# Enable and start services
sudo systemctl enable budget-agent.timer
sudo systemctl start budget-agent.timer
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Built with [DuckDB](https://duckdb.org/) for fast local data processing
- [Streamlit](https://streamlit.io/) for the interactive dashboard
- [Pandas](https://pandas.pydata.org/) for data manipulation

## 📞 Support

For questions or issues:
- Create an issue on GitHub
- Check the configuration examples
- Review the troubleshooting section

---

**Built with ❤️ by [troscity](https://github.com/troscity)**
