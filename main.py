import pandas as pd
import plotly.express as pe
import plotly.graph_objects as go
import yfinance as yf
import streamlit as st
from datetime import datetime, timedelta
from ta.trend import EMAIndicator, SMAIndicator
from ta.volatility import BollingerBands


#----------FUNCTIONALITY----------#

# Extracting data from yahoo's API
def data_extraction(ticker, period, interval):
    end_date = datetime.now()
    if period == "1wk":
        start_date = end_date - timedelta(days=7)
        data = yf.download(tickers=ticker, start=start_date, end=end_date, interval=interval, multi_level_index=False)
    else:
        data = yf.download(tickers=ticker, period=period, interval=interval, multi_level_index=False)
    return data


# Creating metrics from the data extracted.
def metric_extraction(data):

    previous_close = data['Close'].iloc[-1]
    last_close = data['Close'].iloc[0]
    change = ((previous_close-last_close)/previous_close)*100
    volume = data['Volume'].sum()
    period_high = data['High'].max()
    period_low = data['Low'].min()

    return previous_close, last_close, change, volume, period_high, period_low


# Add simple indicators using ta library
def add_indicators(data):

    data['ema_20'] = EMAIndicator(data['Close'], window=20, fillna=True).ema_indicator()
    data['ema_50'] = EMAIndicator(data['Close'], window=50, fillna=True).ema_indicator()
    data['sma_20'] = SMAIndicator(data['Close'], window=20, fillna=True).sma_indicator()
    data['sma_50'] = SMAIndicator(data['Close'], window=50, fillna=True).sma_indicator()
    data['high_bb'] = BollingerBands(close=data['Close'], window=14).bollinger_hband()
    data['low_bb'] = BollingerBands(close=data['Close'], window=14).bollinger_lband()
    return data


#-------------INTERFACE-------------#

# Setting Dashboard interface
st.set_page_config(layout="wide")
st.title("Stock Analysis Dashboard")

st.sidebar.header("Parameters")
ticker = st.sidebar.text_input('Ticker', 'AAPL')
period = st.sidebar.selectbox('Time period', ['1d', '1wk', '1mo', '1y', 'all'])
chart_options = st.sidebar.selectbox('Chart type', ['Candlestick', 'Line'])
indicators = st.sidebar.multiselect('Technical Indicators', ['EMA 20', 'EMA 50', 'SMA 20', 'SMA 50', 'Bollinger Bands'])

# Mapping the frequency of data given a timeframe.
interval_map = {
    '1d': '1m',
    '1wk': '60m',
    '1mo': '1d',
    '1y': '1wk',
    'all': '1wk',
}

# Update dashboard on click
if st.sidebar.button('Update'):

    # Extract data and adding the selected indicators to the Data Frame
    data = data_extraction(ticker, period, interval_map[period])
    data = add_indicators(data)
    df = pd.DataFrame(data)

    # Standardize all stocks columns to be the same
    df = df.reset_index()
    df.rename(columns ={list(df)[0]: "Date"}, inplace=True)

    # Extract metrics from the chosen stock.
    previous_close, last_close, change, volume, period_high, period_low = metric_extraction(df)

    # Display metrics
    st.metric(label=f"{ticker} Last price",
              value=f"{previous_close:.2f} $",
              delta=f"{change: .2f}% change in {period}")
    col1, col2, col3 = st.columns(3)
    col1.metric("High", f"{period_high: .2f} $")
    col2.metric("Low", f"{period_low: .2f} $")
    col3.metric("Volume", f"{volume: ,.0f} $")

    # Plotting the stock price chart
    if chart_options == 'Candlestick':
        fig = go.Figure(data=[
                go.Candlestick( x=df['Date'],
                                open=df['Open'],
                                high=df['High'],
                                low=df['Low'],
                                close=df['Close'],
                                name=f"{ticker} price")
                                ])
    else:
        fig = pe.line(df,
                        x='Date',
                        y='Close',
                        title=f"{ticker} time plot",
                        )

    for indicator in indicators:
        if indicator == 'SMA 20':
            fig.add_trace(go.Scatter(y=df['sma_20'],
                                     x=df['Date'],
                                     name='SMA 20'))
        elif indicator == 'SMA 50':
            fig.add_trace(go.Scatter(y=df['sma_50'],
                                     x=df['Date'],
                                     name='SMA 50'))
        elif indicator == 'EMA 20':
            fig.add_trace(go.Scatter(y=df['ema_20'],
                                     x=df['Date'],
                                     name='EMA 20'))
        elif indicator == 'EMA 50':
            fig.add_trace(go.Scatter(y=df['ema_50'],
                                     x=df['Date'],
                                     name='EMA 50'))
        elif indicator == 'Bollinger Bands':
            fig.add_trace(go.Scatter(x=df['Date'],
                                     y=df['high_bb'],
                                     name='Bollinger Bands',
                                    ))
            fig.add_trace(go.Scatter(x=df['Date'],
                                     y=df['low_bb'],
                                     name='Bollinger Bands',
                                    ))

    # Display charts
    fig.update_layout(title=f"{ticker} price chart",
                      xaxis_title="Date",
                      yaxis_title="Price",
                      xaxis={'rangeslider': {'visible': False}})
    print(df)
    st.plotly_chart(fig)