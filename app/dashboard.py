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
            'transfer_count': 0,
            'transfer_amount': 0,
            'total_transactions': 0,
            'real_transactions': 0
        }
    
    # Exclude internal transfers for real spending calculations
    real_spending = month_data[month_data["internal_transfer"] != True]
    
    income = real_spending[real_spending.amount > 0]['amount'].sum()
    expenses = real_spending[real_spending.amount < 0]['amount'].sum()
    net = income + expenses
    
    # Count internal transfers
    transfers = month_data[month_data["internal_transfer"] == True]
    transfer_count = len(transfers)
    transfer_amount = transfers['amount'].abs().sum()
    
    return {
        'income': income,
        'expenses': expenses,
        'net': net,
        'transfer_count': transfer_count,
        'transfer_amount': transfer_amount,
        'total_transactions': len(month_data),
        'real_transactions': len(real_spending)
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
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Income", f"${month_summary['income']:,.2f}")
    with col2:
        st.metric("Expenses", f"${month_summary['expenses']:,.2f}")
    with col3:
        st.metric("Net", f"${month_summary['net']:,.2f}")
    with col4:
        st.metric("Transactions", month_summary['real_transactions'])
    
    # Show internal transfer info if any
    if month_summary['transfer_count'] > 0:
        st.info(f"⚠️ {month_summary['transfer_count']} internal transfers excluded from calculations (${month_summary['transfer_amount']:,.2f})")
    
    # Monthly breakdown tabs
    tab1, tab2, tab3, tab4 = st.tabs(["📊 Categories", "🏪 Merchants", "💳 Transactions", "📈 Trends"])
    
    with tab1:
        st.subheader("Spending by Category")
        if not month_data.empty:
            real_spending = month_data[month_data["internal_transfer"] != True]
            
            if not real_spending.empty:
                cat_data = real_spending.groupby("category", dropna=False)["amount"].sum().sort_values().to_frame("total").reset_index()
                st.dataframe(cat_data, use_container_width=True)
                
                # Bar chart for categories
                if len(cat_data) > 0:
                    st.subheader("Category Distribution")
                    # Only show expenses for bar chart (negative amounts)
                    expenses_only = cat_data[cat_data['total'] < 0].copy()
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
            real_spending = month_data[month_data["internal_transfer"] != True]
            
            if not real_spending.empty:
                merch_data = real_spending.groupby("merchant")["amount"].agg(['sum', 'count']).reset_index()
                merch_data.columns = ['merchant', 'total', 'count']
                merch_data = merch_data.sort_values('total').head(20)
                st.dataframe(merch_data, use_container_width=True)
            else:
                st.info("No real transactions found for this month")
        else:
            st.info("No transactions found for this month")
    
    with tab3:
        st.subheader("All Transactions")
        if not month_data.empty:
            real_spending = month_data[month_data["internal_transfer"] != True]
            
            if not real_spending.empty:
                # Add filters
                col1, col2 = st.columns(2)
                with col1:
                    min_amount = st.number_input("Min Amount", value=0.0, step=10.0)
                with col2:
                    max_amount = st.number_input("Max Amount", value=10000.0, step=100.0)
                
                # Filter by amount range
                filtered_data = real_spending[
                    (real_spending['amount'] >= min_amount) & 
                    (real_spending['amount'] <= max_amount)
                ]
                
                st.dataframe(
                    filtered_data[['posted_at', 'merchant', 'amount', 'category', 'source']].sort_values("posted_at", ascending=False),
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
                'income': month_summary_trend['income'],
                'expenses': month_summary_trend['expenses'],
                'net': month_summary_trend['net']
            })
        
        if trend_data:
            trend_df = pd.DataFrame(trend_data)
            st.line_chart(trend_df.set_index('month')[['income', 'expenses', 'net']])
            
            # Monthly comparison table
            st.subheader("Monthly Comparison")
            st.dataframe(trend_df, use_container_width=True)
        else:
            st.info("Not enough data for trend analysis")

# Footer
st.markdown("---")
st.markdown("*Powered by Budget Agent*")
