# Internal Transfer & Refund Detection Fixes

## Overview
This document outlines the comprehensive fixes implemented to resolve the critical bugs in the Budget Agent monthly dashboard and report generator where internal transfers were being counted as real income/expenses.

## Issues Fixed

### 1. **Internal Transfers Being Counted as Real Income/Expenses**
- **Problem**: CC repayments, PayPal funding, account sweeps were inflating gross numbers
- **Solution**: Enhanced transfer detection with two-pass approach

### 2. **Refunds Not Separated from Real Income**
- **Problem**: Refunds were being counted as actual income
- **Solution**: Added refund identification and separation logic

### 3. **Dashboard Showing Misleading Numbers**
- **Problem**: Only showed net numbers, hiding the impact of transfers
- **Solution**: Clear separation of gross vs real spending numbers

### 4. **Monthly Data Showing Annual Totals**
- **Problem**: Monthly dashboard was displaying annual-level amounts due to poor date filtering
- **Solution**: Improved monthly filtering with precise date bounds and data validation

## Changes Implemented

### Dashboard (`app/dashboard.py`)
- ✅ Updated `get_monthly_summary()` to properly exclude internal transfers
- ✅ Added refund detection and separation from real income
- ✅ Enhanced UI to show both gross and real spending numbers clearly
- ✅ Added dedicated sections for internal transfers and refunds
- ✅ Improved transaction filtering to exclude transfers from spending analysis
- ✅ Fixed monthly data filtering with precise date bounds
- ✅ Added data validation to catch filtering issues
- ✅ Added annual summary section for yearly totals
- ✅ Added debug information to identify data issues

### Report Generator (`scripts/report_monthly.py`)
- ✅ Mirrored dashboard logic for consistent reporting
- ✅ Added refund separation in monthly reports
- ✅ Enhanced report structure with gross vs real spending sections
- ✅ Added refund tracking in generated reports

### Pipeline (`scripts/run_pipeline.py`)
- ✅ Enhanced `is_internal_transfer()` function with more transfer patterns
- ✅ Added `flag_internal_transfers()` for cross-account pair-matching
- ✅ Added `identify_refunds()` function for refund detection
- ✅ Integrated refund identification into main pipeline
- ✅ Added database schema support for refund flag
- ✅ **NEW**: Enhanced regex patterns for PayPal, CC payments, BPAY, etc.
- ✅ **NEW**: Pair-matching algorithm for equal/opposite amounts across accounts

### New Test Script (`scripts/test_transfers.py`)
- ✅ Created test script to verify transfer detection
- ✅ Shows detected internal transfers and potential pairs
- ✅ Validates refund identification
- ✅ Helps debug transfer detection issues

### New Debug Script (`scripts/debug_data.py`)
- ✅ Created diagnostic script to investigate data filtering issues
- ✅ Shows database schema and date ranges
- ✅ Tests monthly filtering methods
- ✅ Helps identify why monthly data might show annual totals

## How It Works Now

### 1. **First Pass: Enhanced Pattern-Based Detection**
The pipeline identifies transfers using:
- **Enhanced regex patterns**: PayPal "general credit card deposit", CC payments, BPAY, direct debits
- **Keyword matching**: transfer, payment, sweep, etc.
- **Amount patterns**: large round numbers
- **Specific patterns**: PayPal funding, CC payments, account sweeps

### 2. **Second Pass: Cross-Account Pair-Matching**
After initial processing, the system:
- Finds equal/opposite amounts across different accounts
- Matches transactions within 3-day windows (configurable)
- Uses configurable tolerance for amount matching (default: $0.01)
- Marks both sides as internal transfers automatically

### 3. **Refund Detection**
Refunds are identified by:
- Keywords (refund, return, credit, adjustment, reversal)
- Transaction patterns
- Stored in new `is_refund` database column

### 4. **Dashboard Display**
The dashboard now shows:
- **Income**: Excluding refunds and transfers
- **Expenses**: Excluding transfers
- **Refunds**: Separated from real income
- **Internal Transfers**: Dedicated section with counts

## Database Schema Changes

New columns added to `transactions` table:
- `is_refund`: Boolean flag for refund transactions
- `internal_transfer`: Enhanced detection logic

## Usage

### 1. **Process Your Data**
```bash
python -m scripts.run_pipeline
```

### 2. **Test Transfer Detection**
```bash
python -m scripts/test_transfers.py
```

### 3. **Generate Reports**
```bash
python -m scripts.report_monthly --month 2025-08
```

### 4. **View Dashboard**
```bash
streamlit run app/dashboard.py
```

## Benefits

1. **Accurate Spending Analysis**: Real spending numbers exclude internal movements
2. **Robust Transfer Detection**: Two-pass approach with enhanced patterns and pair-matching
3. **Refund Separation**: Clear distinction between income and refunds
4. **Consistent Logic**: Dashboard and reports use identical calculations
5. **Automatic Pair Detection**: Catches transfers even when text isn't obvious

## Testing

After implementing these changes:
1. Run the pipeline to process your CSV files
2. Use the test script to verify transfer detection
3. Check the dashboard for proper number separation
4. Generate monthly reports to confirm consistency

## Future Enhancements

- Machine learning for better transfer pattern recognition
- User-configurable transfer detection rules
- Advanced refund pattern matching
- Transfer pair validation across longer time windows
- Configurable tolerance and window sizes for pair-matching
