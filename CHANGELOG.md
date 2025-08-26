# Changelog

All notable changes to Budget Agent will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Comprehensive documentation and contributing guidelines
- Git repository setup and version control
- Project structure documentation

## [1.0.0] - 2025-01-XX

### Added
- **Core CSV Processing Pipeline**
  - Multi-source CSV ingestion (Ubank, Qantas, PayPal, Apple Pay)
  - Intelligent column detection and mapping
  - Currency formatting support ($ and comma handling)
  - Date parsing for various formats (including Ubank's unique format)

- **Transaction Management**
  - DuckDB database storage with proper schema
  - SHA1 fingerprinting for duplicate prevention
  - Merchant name cleaning and normalization
  - Automatic categorization using regex rules

- **Smart Features**
  - Recurring transaction detection (2+ months in 3 months)
  - Internal transfer identification and filtering
  - Fixed expense flagging
  - Category and subcategory support

- **Reporting & Analytics**
  - Monthly Markdown reports with category breakdowns
  - CSV exports for further analysis
  - Interactive Streamlit dashboard
  - Monthly spending trends and comparisons

- **Configuration System**
  - YAML-based configuration files
  - Flexible source mapping for different banks
  - Merchant categorization rules
  - Category definitions

- **System Integration**
  - Systemd service files for automation
  - Timer-based scheduled processing
  - Command-line interface for all operations

### Technical Features
- **Database**: DuckDB for fast local data processing
- **Data Processing**: Pandas for CSV manipulation and analysis
- **Web Interface**: Streamlit for interactive dashboard
- **Configuration**: PyYAML for configuration management
- **Date Handling**: Robust date parsing with fallback support

### Supported Bank Formats
- **Ubank**: Date and time format, Debit/Credit columns
- **Qantas**: Standard date format, Amount column
- **PayPal**: Date, Name, Amount columns
- **Apple Pay**: Date, Merchant, Amount columns

### Data Schema
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

### Configuration Files
- `config/sources.yaml` - Bank-specific CSV parsing rules
- `config/merchants.yaml` - Merchant categorization patterns
- `config/categories.yaml` - Category and subcategory definitions
- `config/budgets.yaml` - Monthly budget targets (optional)

### Command Line Interface
```bash
# Process CSV files
python -m scripts.run_pipeline

# Generate monthly report
python -m scripts.report_monthly --month 2025-08

# Launch dashboard
streamlit run app/dashboard.py
```

### Dashboard Features
- Monthly overview with income/expenses/net
- Category breakdown with visualizations
- Top merchants analysis
- Transaction filtering and search
- Monthly trends comparison
- Internal transfer transparency

### Report Outputs
- **Markdown Report**: Human-readable monthly summary
- **Category CSV**: Spending breakdown by category
- **Merchant CSV**: Top merchants by spending amount

### Performance Features
- Efficient CSV processing with pandas
- Fast database queries with DuckDB
- Caching for dashboard performance
- Optimized data structures

### Security & Privacy
- Local data storage (no cloud dependencies)
- No external API calls
- Configurable data retention
- Secure transaction fingerprinting

### Deployment Options
- **Local Development**: Direct Python execution
- **Production**: Systemd services for automation
- **Container**: Docker support (future)
- **Cloud**: AWS/GCP deployment (future)

---

## Version History

### v1.0.0 - Initial Release
- Complete CSV processing pipeline
- Multi-bank format support
- Intelligent categorization system
- Interactive dashboard
- Comprehensive reporting
- Production-ready systemd integration

---

## Release Notes

### v1.0.0 Release Notes
This is the initial release of Budget Agent, a comprehensive personal finance management system designed for local-first operation with multi-bank CSV support.

**Key Highlights:**
- 🚀 **Production Ready**: Fully functional system with automated processing
- 🏦 **Multi-Bank Support**: Handles various CSV formats automatically
- 🧠 **Smart Categorization**: AI-like pattern recognition for transactions
- 📊 **Beautiful Reports**: Professional-grade monthly summaries
- 🎯 **Interactive Dashboard**: Modern web interface for analysis
- ⚡ **High Performance**: Fast processing with DuckDB backend

**Getting Started:**
1. Clone the repository
2. Install dependencies with `pip install -r requirements.txt`
3. Place your CSV files in `data/raw/<source>/`
4. Run `python -m scripts.run_pipeline`
5. Generate reports with `python -m scripts.report_monthly --month YYYY-MM`
6. Launch dashboard with `streamlit run app/dashboard.py`

**System Requirements:**
- Python 3.8+
- 4GB RAM (recommended)
- 1GB disk space for database
- Modern web browser for dashboard

**Supported Platforms:**
- Linux (primary)
- macOS
- Windows (with WSL recommended)

---

## Future Roadmap

### v1.1.0 - Enhanced Analytics
- Budget tracking and alerts
- Spending trend analysis
- Export functionality
- Mobile-responsive dashboard

### v1.2.0 - Advanced Features
- Multi-currency support
- Investment tracking
- Tax reporting
- Data backup/restore

### v2.0.0 - Cloud Integration
- Multi-device sync
- Web dashboard
- Mobile app
- API endpoints

---

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for details on how to contribute to Budget Agent.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
