
import os
import streamlit as st

# FRED API Configuration - Uses Streamlit secrets in cloud
def get_fred_api_key():
    """Get FRED API key from Streamlit secrets or environment"""
    try:
        # Try Streamlit secrets first (for cloud deployment)
        return st.secrets["FRED_API_KEY"]
    except:
        # Fall back to environment variable (for local development)
        return os.getenv("FRED_API_KEY", "your_fred_api_key_here")

# Treasury yield series from FRED
TREASURY_SERIES = {
    '1M': 'DGS1MO',
    '3M': 'DGS3MO', 
    '6M': 'DGS6MO',
    '1Y': 'DGS1',
    '2Y': 'DGS2',
    '5Y': 'DGS5',
    '10Y': 'DGS10',
    '30Y': 'DGS30'
}

# Economic indicators
ECONOMIC_INDICATORS = {
    'GDP': 'GDP',
    'Inflation': 'CPIAUCSL',
    'Unemployment': 'UNRATE',
    'Fed_Funds': 'FEDFUNDS',
    'Consumer_Sentiment': 'UMCSENT'
}

# NBER Recession periods (updated through 2023)
RECESSION_PERIODS = [
    ('1969-12-01', '1970-11-01'),
    ('1973-11-01', '1975-03-01'),
    ('1980-01-01', '1980-07-01'),
    ('1981-07-01', '1982-11-01'),
    ('1990-07-01', '1991-03-01'),
    ('2001-03-01', '2001-11-01'),
    ('2007-12-01', '2009-06-01'),
    ('2020-02-01', '2020-04-01')
]

# Analysis parameters
LOOKBACK_YEARS = 10
INVERSION_THRESHOLD = 0.0
MIN_INVERSION_DAYS = 10

# App configuration
APP_TITLE = "Treasury Yield Curve Analyzer"
APP_ICON = "📈"
CACHE_TTL = 3600  # 1 hour cache
