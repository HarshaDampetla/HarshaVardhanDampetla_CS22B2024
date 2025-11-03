import streamlit as st
import plotly.graph_objects as go
import pandas as pd
import time
import analytics as an # Your analytics.py file
import sqlite3

# --- Configuration ---
DB_PATH = 'data/ticks.db'
DEFAULT_SYMBOLS = ['BTCUSDT', 'ETHUSDT']
# ---------------------

# --- Page Configuration ---
st.set_page_config(
    page_title="Quant Analytics Dashboard",
    layout="wide"
)

st.title("📈 Real-Time Quant Analytics Dashboard")

# --- Helper Functions ---

@st.cache_data(ttl=15) # Cache data for 15 seconds
def load_data_from_db(symbols):
    """Load tick data and resample."""
    tick_data = an.load_data(DB_PATH, symbols)
    return tick_data

@st.cache_data(ttl=15)
def get_latest_tick_data(symbols):
    """Gets the single most recent tick for live stats."""
    latest_ticks = {}
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.execute("PRAGMA journal_mode=WAL;")
        for sym in symbols:
            query = f"SELECT timestamp, price FROM ticks WHERE symbol = '{sym}' ORDER BY timestamp DESC LIMIT 1"
            df = pd.read_sql_query(query, conn)
            if not df.empty:
                latest_ticks[sym] = df.iloc[0]
        conn.close()
    except Exception as e:
        print(f"Error getting latest tick: {e}")
    return latest_ticks

# --- Sidebar Controls [cite: 25] ---
st.sidebar.header("Controls")
# Note: For this assignment, we'll hardcode the symbols.
# A real app would query the DB for available symbols.
symbols_to_pair = st.sidebar.multiselect(
    "Select Pair (2 Symbols)",
    DEFAULT_SYMBOLS,
    default=DEFAULT_SYMBOLS
)
timeframe = st.sidebar.selectbox(
    "Select Resampling Timeframe",
    ['1s', '30s', '1min', '5min'], # <-- NOW USES 'min'
    index=2
)

rolling_window = st.sidebar.slider(
    "Rolling Window",
    min_value=10,
    max_value=200,
    value=50
)
regression_type = st.sidebar.radio(
    "Regression Type",
    ['OLS'], # [cite: 15] OLS is the core req. Extensions are bonus.
)

# --- Alerting [cite: 19] ---
st.sidebar.header("Alerts")
z_alert_threshold = st.sidebar.number_input("Z-Score Alert Threshold", value=2.0, step=0.1)

# --- Main Application ---
if len(symbols_to_pair) != 2:
    st.warning("Please select exactly two symbols in the sidebar to form a pair.")
else:
    sym1, sym2 = symbols_to_pair
    
    # Load and process data
    raw_tick_data = load_data_from_db(symbols_to_pair)
    
    if raw_tick_data[sym1].empty or raw_tick_data[sym2].empty:
        st.error("Not enough data in the database. Please let the 'ingest.py' script run for a few minutes.")
    else:
        # Resample data
        df1 = an.resample_data(raw_tick_data[sym1], rule=timeframe)
        df2 = an.resample_data(raw_tick_data[sym2], rule=timeframe)
        
        # --- Analytics Calculations ---
        hedge_ratio, ols_model = an.compute_ols_hedge_ratio(df1, df2)
        spread = an.compute_spread(df1, df2, hedge_ratio)
        zscore = an.compute_zscore(spread)
        rolling_corr = an.compute_rolling_correlation(df1, df2, window=rolling_window)
        
        # Create tabs for different views
        tab_live, tab_pair, tab_stats, tab_export = st.tabs(
            ["Live View", "Pair Analytics", "Statistical Tests", "Data Export"]
        )

        # --- Tab 1: Live View [cite: 17] ---
        with tab_live:
            st.header(f"Live Data Feed")
            
            # Placeholder for live stats
            live_stats_placeholder = st.empty()
            
            # Plotly chart for prices [cite: 16, 24]
            fig_live = go.Figure()
            # Use resampled 'close' for the main chart
            fig_live.add_trace(go.Scatter(x=df1.index, y=df1['close'], mode='lines', name=f"{sym1} ({timeframe})"))
            fig_live.add_trace(go.Scatter(x=df2.index, y=df2['close'], mode='lines', name=f"{sym2} ({timeframe})"))
            fig_live.update_layout(
                title=f"{sym1} / {sym2} Prices",
                xaxis_title="Time", 
                yaxis_title="Price",
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
            )
            # Add zoom/pan/hover [cite: 26]
            st.plotly_chart(fig_live, width='stretch', key="live_prices")
        # --- Tab 2: Pair Analytics [cite: 24] ---
        with tab_pair:
            st.header("Pair Spread & Z-Score")
            
            if spread.empty or zscore.empty:
                st.warning("Could not compute spread or z-score. Not enough aligned data.")
            else:
                # Plot Spread
                fig_spread = go.Figure()
                fig_spread.add_trace(go.Scatter(x=spread.index, y=spread, mode='lines', name='Spread'))
                fig_spread.update_layout(title="Pair Spread (Price - HR * Price)", xaxis_title="Time", yaxis_title="Spread")
                st.plotly_chart(fig_spread, width='stretch', key="spread_chart")
                # Plot Z-Score
                fig_zscore = go.Figure()
                fig_zscore.add_trace(go.Scatter(x=zscore.index, y=zscore, mode='lines', name='Z-Score'))
                # Add alert lines
                fig_zscore.add_hline(y=z_alert_threshold, line_dash="dash", line_color="red", annotation_text="Alert Level")
                fig_zscore.add_hline(y=-z_alert_threshold, line_dash="dash", line_color="red")
                fig_zscore.update_layout(title="Spread Z-Score", xaxis_title="Time", yaxis_title="Z-Score")
                st.plotly_chart(fig_zscore, width='stretch', key="zscore_chart")
            
            st.header("Rolling Correlation")
            if rolling_corr.empty:
                st.warning("Could not compute rolling correlation. Not enough data for window size.")
            else:
                fig_corr = go.Figure()
                fig_corr.add_trace(go.Scatter(x=rolling_corr.index, y=rolling_corr, mode='lines', name='Rolling Correlation'))
                fig_corr.update_layout(title=f"{rolling_window}-Period Rolling Correlation", xaxis_title="Time", yaxis_title="Correlation")
                st.plotly_chart(fig_corr, width='stretch', key="corr_chart")

        # --- Tab 3: Statistical Tests ---
        with tab_stats:
            st.header("Cointegration & Stationarity Tests")
            st.subheader("OLS Regression Results")
            st.subheader("OLS Regression Results")
            if ols_model:
                st.text(f"Hedge Ratio (Slope): {hedge_ratio:.6f}")

                # Check if there are enough data points for the omni_normtest
                if ols_model.nobs < 8:
                    st.warning(f"Not enough data ({int(ols_model.nobs)} samples) for a full statistical summary (like omnitest).")
                    st.text("Please let 'ingest.py' run for longer or choose a smaller timeframe.")
                else:
                    st.text(ols_model.summary())
            else:
                st.warning("Could not compute OLS model.")
                
            st.subheader("Augmented Dickey-Fuller (ADF) Test on Spread [cite: 15]")
            if st.button("Run ADF Test on Spread"):
                if not spread.empty:
                    adf_results = an.run_adf_test(spread)
                    st.json(adf_results)
                    if adf_results.get('p-value') is not None:
                        if adf_results['p-value'] < 0.05:
                            st.success(f"p-value ({adf_results['p-value']:.4f}) is < 0.05. The spread appears to be stationary.")
                        else:
                            st.warning(f"p-value ({adf_results['p-value']:.4f}) is >= 0.05. The spread may not be stationary.")
                else:
                    st.error("Cannot run test: Spread data is empty.")

        # --- Tab 4: Data Export [cite: 20] ---
        with tab_export:
            st.header("Download Processed Data")
            
            # Create a downloadable DataFrame
            export_df = pd.DataFrame({
                f"{sym1}_close": df1['close'],
                f"{sym2}_close": df2['close'],
                "spread": spread,
                "zscore": zscore,
                "rolling_corr": rolling_corr
            }).dropna()
            
            st.dataframe(export_df.tail())
            
            def convert_df_to_csv(df):
                # DO NOT CACHE THIS FUNCTION
                return df.to_csv().encode('utf-8')

            st.download_button(
            label="Download Data as CSV",
            data=convert_df_to_csv(export_df),
            file_name=f"{sym1}_{sym2}_analytics.csv",
            mime="text/csv",
)

        # --- Live Update Loop ---
        # This loop will rerun the whole script, but @st.cache_data
        # prevents reloading all the data every second.
        
        latest_ticks = get_latest_tick_data(symbols_to_pair)
        
        # Calculate live z-score
        live_z = "N/A"
        alert_triggered = False
        
        if sym1 in latest_ticks and sym2 in latest_ticks and hedge_ratio is not None and not spread.empty:
            live_spread = latest_ticks[sym1]['price'] - hedge_ratio * latest_ticks[sym2]['price']
            live_z_val = (live_spread - spread.mean()) / spread.std()
            live_z = f"{live_z_val:.4f}"
            
            if abs(live_z_val) > z_alert_threshold:
                alert_triggered = True

        # Update the live stats placeholder
        with live_stats_placeholder.container():
            cols = st.columns(3)
            cols[0].metric(label=f"Live {sym1}", value=f"{latest_ticks.get(sym1, {}).get('price', 0):.2f}")
            cols[1].metric(label=f"Live {sym2}", value=f"{latest_ticks.get(sym2, {}).get('price', 0):.2f}")
            cols[2].metric(label="Live Z-Score", value=live_z)
            
            if alert_triggered:
                st.error(f"🚨 ALERT: Live Z-Score ({live_z}) has breached threshold ({z_alert_threshold})")
        
        # Rerun the app every 5 seconds for a near-real-time feel [cite: 18]
        time.sleep(5)
        st.rerun()