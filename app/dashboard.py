import os
import duckdb
import pandas as pd
import streamlit as st
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "db", "ledger.duckdb")

@st.cache_data
def load_df():
    con = duckdb.connect(DB_PATH, read_only=True)
    df = con.execute("SELECT * FROM transactions").fetchdf()
    df["posted_at"] = pd.to_datetime(df["posted_at"])
    return df

@st.cache_data
def get_monthly_data(selected_month):
    """Get data for a specific month directly from database"""
    con = duckdb.connect(DB_PATH, read_only=True)
    
    # Query only the selected month's data
    month_data = con.execute(f"""
        SELECT * FROM transactions 
        WHERE strftime('%Y-%m', posted_at) = '{selected_month}'
    """).fetchdf()
    
    con.close()
    
    if not month_data.empty:
        month_data["posted_at"] = pd.to_datetime(month_data["posted_at"])
    
    return month_data

@st.cache_data
def get_monthly_summary(month_data):
    """Get monthly summary for the provided month data"""
    if month_data.empty:
        return {
            'income': 0,
            'expenses': 0,
            'net': 0,
            'refunds': 0,
            'transfer_count': 0,
            'transfer_amount': 0,
            'total_transactions': 0,
            'real_transactions': 0
        }
    
    # Exclude internal transfers
    real = month_data[month_data["internal_transfer"] != True]
    
    # Treat refunds separately so "Income" reflects actual earnings
    refunds = real[
        (real["category"] == "Income") & (real["subcategory"] == "Refunds")
    ]["amount"].sum()
    
    income = real[
        (real["amount"] > 0) &
        ~((real["category"] == "Income") & (real["subcategory"] == "Refunds"))
    ]["amount"].sum()
    
    expenses = real[real["amount"] < 0]["amount"].sum()
    
    net = income + expenses + refunds
    
    # Count internal transfers
    transfers = month_data[month_data["internal_transfer"] == True]
    transfer_count = len(transfers)
    transfer_amount = transfers['amount'].abs().sum()
    
    return {
        'income': income,
        'expenses': expenses,
        'net': net,
        'refunds': refunds,
        'transfer_count': transfer_count,
        'transfer_amount': transfer_amount,
        'total_transactions': len(month_data),
        'real_transactions': len(real)
    }

@st.cache_data
def get_available_months():
    """Get list of available months from database"""
    con = duckdb.connect(DB_PATH, read_only=True)
    months = con.execute("""
        SELECT DISTINCT strftime('%Y-%m', posted_at) as month 
        FROM transactions 
        ORDER BY month
    """).fetchdf()['month'].tolist()
    con.close()
    return months

st.title("Budget Agent — Monthly Dashboard")
st.markdown("View your spending and income for each month")

# Get available months and default to current month
months = get_available_months()
if not months:
    st.info("No data yet. Ingest some CSVs then refresh.")
else:
    current_month = datetime.now().strftime("%Y-%m")
    
    # Default to current month if available, otherwise most recent
    default_index = months.index(current_month) if current_month in months else len(months) - 1
    
    # Month selector
    selected_month = st.selectbox(
        "Select Month", 
        months, 
        index=default_index,
        help="Choose a month to view detailed spending and income data"
    )
    
    # Get monthly data and summary
    month_data = get_monthly_data(selected_month)
    month_summary = get_monthly_summary(month_data)
    
    # Display monthly overview
    st.header(f"📅 {selected_month} Overview")
    
    # Show real spending numbers (excluding transfers and refunds)
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Income (excl. refunds)", f"${month_summary['income']:,.2f}")
    with col2:
        st.metric("Expenses (excl. transfers)", f"${month_summary['expenses']:,.2f}")
    with col3:
        st.metric("Net", f"${month_summary['net']:,.2f}")
    with col4:
        st.metric("Real Transactions", month_summary['real_transactions'])
    
    # Show refunds and transfers info
    if month_summary['refunds'] > 0 or month_summary['transfer_count'] > 0:
        col1, col2 = st.columns(2)
        with col1:
            if month_summary['refunds'] > 0:
                st.metric("Refunds", f"${month_summary['refunds']:,.2f}")
        with col2:
            if month_summary['transfer_count'] > 0:
                st.metric("Internal Transfers", f"${month_summary['transfer_amount']:,.2f}")
                st.caption(f"{month_summary['transfer_count']} transactions excluded")
    
    # Show internal transfer info if any
    if month_summary['transfer_count'] > 0:
        st.info(f"⚠️ {month_summary['transfer_count']} internal transfers excluded from real spending calculations (${month_summary['transfer_amount']:,.2f})")
    
    # Show refunds if any
    if month_summary['refunds'] > 0:
        st.info(f"💸 {month_summary['refunds']:,.2f} in refunds have been separated from real income")
    
    # Monthly breakdown tabs
    tab1, tab2, tab3, tab4 = st.tabs(["📊 Categories", "🏪 Merchants", "💳 Transactions", "📈 Trends"])
    
    with tab1:
        st.subheader("Spending by Category")
        if not month_data.empty:
            # Use same logic as get_monthly_summary
            real = month_data[month_data["internal_transfer"] != True]
            
            if not real.empty:
                # Group by category, excluding refunds from income calculations
                cat_data = real.groupby("category", dropna=False).apply(
                    lambda x: pd.Series({
                        'total': x['amount'].sum(),
                        'count': len(x),
                        'is_refund': ((x['category'] == 'Income') & (x['subcategory'] == 'Refunds')).any()
                    })
                ).reset_index()
                
                # Separate refunds for display
                refunds_data = cat_data[cat_data['is_refund'] == True].copy()
                non_refunds_data = cat_data[cat_data['is_refund'] != True].copy()
                
                st.dataframe(non_refunds_data[['category', 'total', 'count']], use_container_width=True)
                
                # Show refunds separately if any
                if not refunds_data.empty:
                    st.subheader("Refunds by Category")
                    st.dataframe(refunds_data[['category', 'total', 'count']], use_container_width=True)
                
                # Bar chart for categories (excluding refunds)
                if len(non_refunds_data) > 0:
                    st.subheader("Category Distribution (excluding refunds)")
                    # Only show expenses for bar chart (negative amounts)
                    expenses_only = non_refunds_data[non_refunds_data['total'] < 0].copy()
                    if not expenses_only.empty:
                        expenses_only['total'] = expenses_only['total'].abs()  # Make positive for display
                        st.bar_chart(expenses_only.set_index('category')['total'])
            else:
                st.info("No real transactions found for this month")
        else:
            st.info("No transactions found for this month")
    
    with tab2:
        st.subheader("Top Merchants by Spending")
        if not month_data.empty:
            # Use same logic as get_monthly_summary
            real = month_data[month_data["internal_transfer"] != True]
            
            if not real.empty:
                # Group by merchant, excluding refunds from income calculations
                merch_data = real.groupby("merchant").apply(
                    lambda x: pd.Series({
                        'total': x['amount'].sum(),
                        'count': len(x),
                        'is_refund': ((x['category'] == 'Income') & (x['subcategory'] == 'Refunds')).any()
                    })
                ).reset_index()
                
                # Separate refunds for display
                refunds_merch = merch_data[merch_data['is_refund'] == True].copy()
                non_refunds_merch = merch_data[merch_data['is_refund'] != True].copy()
                
                # Show non-refund merchants
                st.subheader("Merchants (excluding refunds)")
                non_refunds_merch = non_refunds_merch.sort_values('total').head(20)
                st.dataframe(non_refunds_merch[['merchant', 'total', 'count']], use_container_width=True)
                
                # Show refund merchants separately if any
                if not refunds_merch.empty:
                    st.subheader("Refund Merchants")
                    refunds_merch = refunds_merch.sort_values('total', ascending=False).head(10)
                    st.dataframe(refunds_merch[['merchant', 'total', 'count']], use_container_width=True)
            else:
                st.info("No real transactions found for this month")
        else:
            st.info("No transactions found for this month")
    
    with tab3:
        st.subheader("All Transactions")
        if not month_data.empty:
            # Use same logic as get_monthly_summary
            real = month_data[month_data["internal_transfer"] != True]
            
            if not real.empty:
                # Add filters
                col1, col2 = st.columns(2)
                with col1:
                    min_amount = st.number_input("Min Amount", value=0.0, step=10.0)
                with col2:
                    max_amount = st.number_input("Max Amount", value=10000.0, step=100.0)
                
                # Filter by amount range
                filtered_data = real[
                    (real['amount'] >= min_amount) & 
                    (real['amount'] <= max_amount)
                ]
                
                # Separate refunds for display
                refunds_txns = filtered_data[
                    (filtered_data["category"] == "Income") & 
                    (filtered_data["subcategory"] == "Refunds")
                ]
                non_refunds_txns = filtered_data[
                    ~((filtered_data["category"] == "Income") & 
                      (filtered_data["subcategory"] == "Refunds"))
                ]
                
                # Show non-refund transactions
                st.subheader("Transactions (excluding refunds)")
                st.dataframe(
                    non_refunds_txns[['posted_at', 'merchant', 'amount', 'category', 'source']].sort_values("posted_at", ascending=False),
                    use_container_width=True
                )
                
                # Show refund transactions separately if any
                if not refunds_txns.empty:
                    st.subheader("Refund Transactions")
                    st.dataframe(
                        refunds_txns[['posted_at', 'merchant', 'amount', 'category', 'source']].sort_values("posted_at", ascending=False),
                        use_container_width=True
                    )
            else:
                st.info("No real transactions found for this month")
        else:
            st.info("No transactions found for this month")
    
    with tab4:
        st.subheader("Monthly Trends")
        # Show last 6 months of data
        recent_months = months[-6:] if len(months) >= 6 else months
        
        trend_data = []
        for month in recent_months:
            month_data_trend = get_monthly_data(month)
            month_summary_trend = get_monthly_summary(month_data_trend)
            trend_data.append({
                'month': month,
                'income': month_summary_trend['income'],  # Already excludes refunds
                'expenses': month_summary_trend['expenses'],  # Already excludes transfers
                'net': month_summary_trend['net'],
                'refunds': month_summary_trend['refunds']
            })
        
        if trend_data:
            trend_df = pd.DataFrame(trend_data)
            
            # Show trends excluding refunds for income
            st.subheader("Income & Expenses (excluding refunds & transfers)")
            st.line_chart(trend_df.set_index('month')[['income', 'expenses', 'net']])
            
            # Show refunds trend separately
            if trend_df['refunds'].sum() > 0:
                st.subheader("Refunds Trend")
                st.line_chart(trend_df.set_index('month')['refunds'])
            
            # Monthly comparison table
            st.subheader("Monthly Comparison")
            st.dataframe(trend_df, use_container_width=True)
        else:
            st.info("Not enough data for trend analysis")

# Footer
st.markdown("---")
st.markdown("*Powered by Budget Agent*")
