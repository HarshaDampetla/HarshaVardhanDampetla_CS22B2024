import pandas as pd
import numpy as np
import statsmodels.api as sm
from statsmodels.tsa.stattools import adfuller
import sqlite3

def load_data(db_path, symbols, max_rows=500000):
    """
    Loads tick data from SQLite into a dictionary of pandas DataFrames.
    Loads only the most recent `max_rows` to keep memory usage low.
    """
    data = {}
    try:
        conn = sqlite3.connect(db_path)
        conn.execute("PRAGMA journal_mode=WAL;")
        for sym in symbols:
            # Query for the most recent N rows for the specific symbol
            query = f"""
            SELECT * FROM (
                SELECT timestamp, price, size
                FROM ticks
                WHERE symbol = '{sym}'
                ORDER BY timestamp DESC
                LIMIT {max_rows}
            )
            ORDER BY timestamp ASC;
            """
            df = pd.read_sql_query(query, conn)
            
            if not df.empty:
                # Convert timestamp (ms) to datetime and set as index
                df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
                df = df.set_index('timestamp')
                data[sym] = df
            else:
                data[sym] = pd.DataFrame(columns=['price', 'size']) # Empty df
                
    except Exception as e:
        print(f"Error loading data: {e}")
    finally:
        if conn:
            conn.close()
    return data

def resample_data(tick_df, rule='1Min'):
    """
    Resamples tick data into OHLCV bars for a given timeframe. [cite: 14]
    """
    if tick_df.empty:
        return pd.DataFrame()
        
    # Resample price to OHLC
    ohlc = tick_df['price'].resample(rule).ohlc()
    # Resample size to Volume (sum)
    volume = tick_df['size'].resample(rule).sum().rename('volume')
    
    # Combine and return
    resampled_df = ohlc.join(volume, how='outer')
    return resampled_df

def compute_ols_hedge_ratio(df1, df2):
    """
    Calculates the hedge ratio between two price series using OLS.
    """
    # Ensure data is aligned by index (timestamp)
    aligned_df = df1.join(df2, how='inner', lsuffix='_1', rsuffix='_2')

    # --- ADD THIS LINE TO FIX THE ERROR ---
    # Drop any rows where 'close' price is NaN for either symbol
    aligned_df = aligned_df.dropna(subset=['close_1', 'close_2'])
    
    if aligned_df.empty or len(aligned_df) < 2:
        return None, None
    
    # Use 'close' prices from resampled data
    y = aligned_df['close_1']
    X = sm.add_constant(aligned_df['close_2'])
    
    model = sm.OLS(y, X).fit()
    hedge_ratio = model.params.iloc[1] # Use .iloc[1] for positional access
    
    return hedge_ratio, model

def compute_spread(df1, df2, hedge_ratio):
    """
    Calculates the spread between two series. [cite: 15]
    """
    if hedge_ratio is None:
        return pd.Series(dtype=np.float64)
        
    aligned_df = df1.join(df2, how='inner', lsuffix='_1', rsuffix='_2')
    
    if aligned_df.empty:
        return pd.Series(dtype=np.float64)
        
    spread = aligned_df['close_1'] - hedge_ratio * aligned_df['close_2']
    spread = spread.rename('spread')
    return spread

def compute_zscore(spread_series):
    """
    Calculates the z-score of the spread. [cite: 15]
    """
    if spread_series.empty or spread_series.std() == 0:
        return pd.Series(dtype=np.float64)
        
    mean = spread_series.mean()
    std = spread_series.std()
    zscore = (spread_series - mean) / std
    return zscore.rename('zscore')

def compute_rolling_correlation(df1, df2, window=50):
    """
    Computes the rolling correlation between two price series. [cite: 15]
    """
    aligned_df = df1.join(df2, how='inner', lsuffix='_1', rsuffix='_2')
    
    if aligned_df.empty or len(aligned_df) < window:
        return pd.Series(dtype=np.float64)
        
    return aligned_df['close_1'].rolling(window).corr(aligned_df['close_2']).rename('correlation')

def run_adf_test(series):
    """
    Runs the Augmented Dickey-Fuller test on a series. [cite: 15]
    """
    if series.empty:
        return {"error": "No data to test."}
        
    # Drop NaNs which can break the test
    series_cleaned = series.dropna()
    
    if series_cleaned.empty:
        return {"error": "Data is all NaN."}
        
    try:
        result = adfuller(series_cleaned)
        return {
            'ADF Statistic': result[0],
            'p-value': result[1],
            '# Lags Used': result[2],
            '# Observations': result[3],
            'Critical Values': result[4]
        }
    except Exception as e:
        return {"error": f"ADF test failed: {e}"}