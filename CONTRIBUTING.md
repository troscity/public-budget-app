# Contributing to Budget Agent 🤝

Thank you for your interest in contributing to Budget Agent! This document provides guidelines and information for contributors.

## 🚀 Getting Started

### Prerequisites
- Python 3.8+
- Git
- Basic understanding of Python, YAML, and SQL

### Development Setup
```bash
# 1. Fork and clone the repository
git clone https://github.com/YOUR_USERNAME/budget-agent.git
cd budget-agent

# 2. Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Install development dependencies
pip install pytest black flake8 mypy

# 5. Set up pre-commit hooks (optional)
pre-commit install
```

## 📋 Contribution Guidelines

### What We're Looking For
- **Bug fixes** - Fix issues and improve reliability
- **Feature enhancements** - Add new functionality
- **Documentation** - Improve docs and examples
- **Testing** - Add tests and improve coverage
- **Performance** - Optimize processing speed
- **Configuration** - Add support for new bank formats

### What We're NOT Looking For
- **Personal data** - Never commit real financial data
- **API keys** - Don't commit sensitive credentials
- **Large binary files** - Keep the repo lightweight

## 🔧 Development Workflow

### 1. Create a Feature Branch
```bash
git checkout -b feature/your-feature-name
# or
git checkout -b fix/issue-description
```

### 2. Make Your Changes
- Follow the existing code style
- Add tests for new functionality
- Update documentation as needed
- Ensure all tests pass

### 3. Test Your Changes
```bash
# Run the test suite
pytest

# Check code quality
black --check .
flake8 .
mypy .

# Test the pipeline
python -m scripts.run_pipeline
python -m scripts.report_monthly --month 2025-08
streamlit run app/dashboard.py
```

### 4. Commit Your Changes
```bash
git add .
git commit -m "feat: add support for new bank format

- Add new source configuration for Bank XYZ
- Update CSV parsing logic for date format
- Add tests for new functionality
- Update documentation"
```

### 5. Push and Create PR
```bash
git push origin feature/your-feature-name
```

Then create a Pull Request on GitHub with:
- Clear description of changes
- Screenshots if UI changes
- Test results
- Any breaking changes noted

## 📁 Project Structure

### Key Directories
- **`app/`** - Main application files
- **`config/`** - Configuration templates and examples
- **`scripts/`** - Core processing scripts
- **`tests/`** - Test files (when added)
- **`docs/`** - Additional documentation

### Important Files
- **`scripts/run_pipeline.py`** - Main CSV processing logic
- **`scripts/common.py`** - Shared utilities and database functions
- **`app/dashboard.py`** - Streamlit dashboard
- **`config/sources.yaml`** - Bank format definitions

## 🧪 Testing

### Running Tests
```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_pipeline.py

# Run with coverage
pytest --cov=scripts --cov=app

# Run tests in parallel
pytest -n auto
```

### Writing Tests
- Place tests in `tests/` directory
- Name test files `test_*.py`
- Use descriptive test names
- Mock external dependencies
- Test both success and failure cases

### Example Test
```python
def test_csv_parsing_with_ubank_format():
    """Test that Ubank CSV format is parsed correctly"""
    # Arrange
    csv_content = "Date and time,Description,Debit,Credit\n13:26 25-08-25,Test,-100,"
    
    # Act
    result = parse_csv_content(csv_content, ubank_config)
    
    # Assert
    assert len(result) == 1
    assert result[0]['amount'] == -100.0
    assert result[0]['merchant'] == 'Test'
```

## 📝 Code Style

### Python
- Follow [PEP 8](https://pep8.org/) style guide
- Use type hints where possible
- Keep functions small and focused
- Add docstrings for public functions

### YAML Configuration
- Use consistent indentation (2 spaces)
- Group related settings together
- Add comments for complex configurations
- Use descriptive key names

### Example
```python
def process_transactions(transactions: List[Dict], 
                        rules: Dict[str, Any]) -> List[Dict]:
    """
    Process transactions using categorization rules.
    
    Args:
        transactions: List of transaction dictionaries
        rules: Categorization rules configuration
        
    Returns:
        List of processed transactions with categories
        
    Raises:
        ValueError: If rules configuration is invalid
    """
    if not rules:
        raise ValueError("Rules configuration cannot be empty")
    
    processed = []
    for txn in transactions:
        processed.append(apply_rules(txn, rules))
    
    return processed
```

## 🔍 Debugging

### Common Issues
1. **CSV Parsing Errors**
   - Check column names in `config/sources.yaml`
   - Verify date format compatibility
   - Test with sample data

2. **Database Errors**
   - Ensure DuckDB is properly installed
   - Check database file permissions
   - Verify schema matches code

3. **Dashboard Issues**
   - Check Streamlit version compatibility
   - Verify data exists in database
   - Check browser console for errors

### Debug Tools
```bash
# Enable debug logging
export DEBUG=1
python -m scripts.run_pipeline

# Check database contents
python -c "import duckdb; con = duckdb.connect('db/ledger.duckdb'); print(con.execute('SELECT COUNT(*) FROM transactions').fetchone()[0])"

# Validate configuration
python -c "from scripts.common import load_yaml; print(load_yaml('sources.yaml'))"
```

## 📚 Documentation

### What to Document
- **New features** - How to use and configure
- **Configuration options** - What each setting does
- **API changes** - Breaking changes and migrations
- **Examples** - Real-world usage scenarios

### Documentation Standards
- Use clear, concise language
- Include code examples
- Add screenshots for UI changes
- Update README.md for major changes
- Keep configuration examples up-to-date

## 🚀 Release Process

### Versioning
We use [Semantic Versioning](https://semver.org/):
- **MAJOR** - Breaking changes
- **MINOR** - New features, backward compatible
- **PATCH** - Bug fixes, backward compatible

### Release Checklist
- [ ] All tests pass
- [ ] Documentation updated
- [ ] Changelog updated
- [ ] Version bumped
- [ ] Release notes written
- [ ] GitHub release created

## 🤝 Community Guidelines

### Be Respectful
- Use inclusive language
- Be patient with newcomers
- Provide constructive feedback
- Help others learn and grow

### Communication
- Use GitHub Issues for bugs and features
- Use GitHub Discussions for questions
- Be clear and specific in your requests
- Respond to feedback and questions

## 📞 Getting Help

### Resources
- **GitHub Issues** - Report bugs and request features
- **GitHub Discussions** - Ask questions and share ideas
- **README.md** - Project overview and quick start
- **Code comments** - Inline documentation

### Before Asking
1. Check existing issues and discussions
2. Read the relevant documentation
3. Try to reproduce the issue
4. Provide clear steps and error messages

## 🎯 Contribution Ideas

### Good First Issues
- Add support for new bank formats
- Improve error messages
- Add more configuration examples
- Enhance test coverage
- Fix typos in documentation

### Advanced Features
- Add budget tracking and alerts
- Implement data export functionality
- Add more visualization options
- Create mobile-friendly interface
- Add data backup and restore

## 📄 License

By contributing to Budget Agent, you agree that your contributions will be licensed under the same license as the project (MIT License).

---

**Thank you for contributing to Budget Agent! 🚀**

Your contributions help make personal finance management easier and more accessible for everyone.
