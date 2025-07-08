
import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import datetime, timedelta
import sys
import os

# Add src directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from data_collector import TreasuryDataCollector
import config

# Configure Streamlit page
st.set_page_config(
    page_title=config.APP_TITLE,
    page_icon=config.APP_ICON,
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 1rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
        border-left: 4px solid #1f77b4;
    }
    .status-normal {
        background-color: #d4edda;
        color: #155724;
        padding: 0.5rem;
        border-radius: 0.25rem;
    }
    .status-warning {
        background-color: #fff3cd;
        color: #856404;
        padding: 0.5rem;
        border-radius: 0.25rem;
    }
    .status-danger {
        background-color: #f8d7da;
        color: #721c24;
        padding: 0.5rem;
        border-radius: 0.25rem;
    }
</style>
""", unsafe_allow_html=True)

def create_yield_curve_chart(yields_df, compare_dates=None):
    """Create interactive yield curve chart"""
    if yields_df.empty:
        return None
    
    fig = go.Figure()
    
    maturities = ['1M', '3M', '6M', '1Y', '2Y', '5Y', '10Y', '30Y']
    maturity_years = [1/12, 0.25, 0.5, 1, 2, 5, 10, 30]
    
    # Current curve
    latest_date = yields_df.index[-1]
    latest_yields = yields_df.iloc[-1]
    
    current_x = []
    current_y = []
    
    for i, mat in enumerate(maturities):
        if mat in latest_yields.index and pd.notna(latest_yields[mat]):
            current_x.append(maturity_years[i])
            current_y.append(latest_yields[mat])
    
    fig.add_trace(go.Scatter(
        x=current_x,
        y=current_y,
        mode='lines+markers',
        name=f'Current ({latest_date.strftime("%Y-%m-%d")})',
        line=dict(color='#1f77b4', width=3),
        marker=dict(size=8)
    ))
    
    # Add comparison curves if requested
    if compare_dates:
        colors = ['#ff7f0e', '#2ca02c', '#d62728']
        for i, date in enumerate(compare_dates):
            if date in yields_df.index:
                compare_yields = yields_df.loc[date]
                comp_x = []
                comp_y = []
                
                for j, mat in enumerate(maturities):
                    if mat in compare_yields.index and pd.notna(compare_yields[mat]):
                        comp_x.append(maturity_years[j])
                        comp_y.append(compare_yields[mat])
                
                fig.add_trace(go.Scatter(
                    x=comp_x,
                    y=comp_y,
                    mode='lines+markers',
                    name=date.strftime("%Y-%m-%d"),
                    line=dict(color=colors[i % len(colors)], width=2),
                    marker=dict(size=6)
                ))
    
    fig.update_layout(
        title="Treasury Yield Curve",
        xaxis_title="Maturity (Years)",
        yaxis_title="Yield (%)",
        height=500,
        template="plotly_white",
        xaxis=dict(type='log'),
        hovermode='x unified'
    )
    
    return fig

def create_spread_chart(yields_df):
    """Create yield spread time series chart"""
    if yields_df.empty:
        return None
    
    fig = go.Figure()
    
    # 2Y-10Y spread
    if '2Y' in yields_df.columns and '10Y' in yields_df.columns:
        spread_2y10y = yields_df['2Y'] - yields_df['10Y']
        fig.add_trace(go.Scatter(
            x=spread_2y10y.index,
            y=spread_2y10y.values,
            name='2Y-10Y Spread',
            line=dict(color='#1f77b4', width=2)
        ))
    
    # 3M-10Y spread
    if '3M' in yields_df.columns and '10Y' in yields_df.columns:
        spread_3m10y = yields_df['3M'] - yields_df['10Y']
        fig.add_trace(go.Scatter(
            x=spread_3m10y.index,
            y=spread_3m10y.values,
            name='3M-10Y Spread',
            line=dict(color='#ff7f0e', width=2)
        ))
    
    # Add zero line
    fig.add_hline(y=0, line_dash="dash", line_color="red")
    
    # Add recession shading
    for start_str, end_str in config.RECESSION_PERIODS:
        start_date = pd.to_datetime(start_str)
        end_date = pd.to_datetime(end_str)
        
        if start_date >= yields_df.index[0]:
            fig.add_vrect(
                x0=start_date, x1=end_date,
                fillcolor="gray", opacity=0.2,
                line_width=0
            )
    
    fig.update_layout(
        title="Yield Curve Spreads with Recession Periods",
        xaxis_title="Date",
        yaxis_title="Spread (bps)",
        height=400,
        template="plotly_white",
        showlegend=True
    )
    
    return fig

def main():
    # Header
    st.markdown(f'<div class="main-header">{config.APP_TITLE}</div>', unsafe_allow_html=True)
    
    # Sidebar
    st.sidebar.title("📊 Treasury Analytics")
    
    # Initialize data collector
    collector = TreasuryDataCollector()
    
    # Health check
    health_ok, health_msg = collector.health_check()
    if not health_ok:
        st.error(f"❌ Data connection failed: {health_msg}")
        st.info("Please check your FRED API key configuration in Streamlit secrets")
        st.stop()
    
    # Data loading section
    st.sidebar.subheader("📈 Data Controls")
    
    if st.sidebar.button("🔄 Refresh Data"):
        st.cache_data.clear()
        st.experimental_rerun()
    
    # Load data
    with st.spinner("Loading Treasury data..."):
        yields_df = collector.get_treasury_yields()
        
    if yields_df.empty:
        st.error("Failed to load yield data. Please check your connection and try again.")
        st.stop()
    
    # Calculate metrics
    metrics = collector.calculate_yield_curve_metrics(yields_df)
    inversions = collector.identify_inversions(yields_df)
    
    # Current status
    st.subheader("📊 Current Market Status")
    
    if not yields_df.empty:
        latest_date = yields_df.index[-1]
        latest_yields = yields_df.iloc[-1]
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                label="10Y Treasury",
                value=f"{latest_yields.get('10Y', 0):.2f}%",
                delta=f"{(latest_yields.get('10Y', 0) - yields_df['10Y'].iloc[-30:-1].mean()):.2f}% (30d avg)"
            )
        
        with col2:
            st.metric(
                label="2Y Treasury", 
                value=f"{latest_yields.get('2Y', 0):.2f}%",
                delta=f"{(latest_yields.get('2Y', 0) - yields_df['2Y'].iloc[-30:-1].mean()):.2f}% (30d avg)"
            )
        
        with col3:
            spread_2y10y = latest_yields.get('2Y', 0) - latest_yields.get('10Y', 0)
            st.metric(
                label="2Y-10Y Spread",
                value=f"{spread_2y10y:.0f} bps",
                delta="Inverted" if spread_2y10y < 0 else "Normal"
            )
        
        with col4:
            curve_status = "🔴 Inverted" if spread_2y10y < 0 else "🟢 Normal"
            st.metric(
                label="Curve Status",
                value=curve_status
            )
    
    # Main charts
    st.subheader("📈 Yield Curve Analysis")
    
    # Yield curve chart
    curve_chart = create_yield_curve_chart(yields_df)
    if curve_chart:
        st.plotly_chart(curve_chart, use_container_width=True)
    
    # Spread chart
    spread_chart = create_spread_chart(yields_df)
    if spread_chart:
        st.plotly_chart(spread_chart, use_container_width=True)
    
    # Historical analysis
    st.subheader("📊 Historical Analysis")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("**Recent Inversions:**")
        if inversions:
            for inv in inversions[-3:]:  # Show last 3 inversions
                st.write(f"• {inv['start'].strftime('%Y-%m-%d')} to {inv['end'].strftime('%Y-%m-%d')}")
                st.write(f"  Duration: {inv['duration_days']} days")
                st.write(f"  Max inversion: {inv['max_inversion']:.0f} bps")
        else:
            st.write("No significant inversions found in recent data.")
    
    with col2:
        st.write("**Key Statistics:**")
        if not yields_df.empty:
            st.write(f"• Data period: {yields_df.index[0].strftime('%Y-%m-%d')} to {yields_df.index[-1].strftime('%Y-%m-%d')}")
            st.write(f"• Total observations: {len(yields_df):,}")
            if '10Y' in yields_df.columns:
                st.write(f"• 10Y yield range: {yields_df['10Y'].min():.2f}% - {yields_df['10Y'].max():.2f}%")
            st.write(f"• Historical inversions: {len(inversions)}")
    
    # Footer
    st.markdown("---")
    st.markdown("**Data Source:** Federal Reserve Economic Data (FRED)")
    st.markdown(f"**Last Updated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    main()
