import yfinance as yf
import pandas as pd
import pandas_ta as ta
import numpy as np
from datetime import datetime as dt
from datetime import timedelta as delta
import numpy as np
import seaborn as sb
import os
import matplotlib.pyplot as plt

signals = pd.DataFrame({
    '10_cross_30':[0,0,1,1,1],
    'MACD_Signal_MACD':[1,1,1,0,0],
    'MACD_lim':[0,0,0,1,1],
    'abv_50':[1,1,1,0,0],
    'abv_200':[0,1,0,0,1],
    'strategy': [1,2,3,4,5],
})

nifty_50_stocks = ['TSLA', 'AAPL', 'GOOG', 'QCOM', 'MSFT', 'NVDA', 'META']

def add_signal_indicators(df):
    df['SMA_10'] = ta.sma(df['Adj Close'],length=10)
    df['SMA_30'] = ta.sma(df['Adj Close'],length=30)
    df['SMA_50'] = ta.sma(df['Adj Close'],length=50)
    df['SMA_200'] = ta.sma(df['Adj Close'],length=200)

    macd = ta.macd(df['Adj Close'], fast=12, slow=26, signal=9)
    df['MACD'] = macd['MACD_12_26_9']
    df['MACD_signal'] = macd['MACDs_12_26_9']
    df['MACD_hist'] = macd['MACDh_12_26_9']

    df['10_cross_30'] = np.where(df['SMA_10'] > df['SMA_30'], 1, 0)

    df['MACD_Signal_MACD'] = np.where(df['MACD_signal'] < df['MACD'], 1, 0)

    df['MACD_lim'] = np.where(df['MACD']>0, 1, 0)

    df['abv_50'] = np.where((df['SMA_30']>df['SMA_50'])
                            &(df['SMA_10']>df['SMA_50']), 1, 0)

    df['abv_200'] = np.where((df['SMA_30']>df['SMA_200'])
                            &(df['SMA_10']>df['SMA_200'])
                            &(df['SMA_50']>df['SMA_200']), 1, 0)

    return df

def backtest_signals(row):
    global TRADES, trade_in_progress, signals, holding_period

    if(trade_in_progress):
        _data = TRADES[-1]
        # time to sell after n holding days
        if(row['index']==_data['sell_index']):
            _data['sell_price'] = round(row['Adj Close'],2)
            _data['sell_date'] = str(pd.to_datetime(row['Date']).date())
            _data['returns'] = round((_data['sell_price']-_data['buy_price'])/_data['buy_price']*100, 3)
            TRADES[-1] = _data
            trade_in_progress = False

    else:
        _r = pd.DataFrame([row])
        _r = _r.merge(signals, on=list(signals.columns[:-1]), how='inner')
        strategy = _r.shape[0]

        if(strategy>0):
            trade_in_progress = True
            TRADES.append({
                'strategy': _r['strategy'].values[0],
                'buy_date': str(pd.to_datetime(row['Date']).date()),
                'buy_index': row['index'],
                'sell_date': '',
                'sell_index': row['index'] + holding_period,
                'buy_price': round(row['Adj Close'], 2),
                'sell_price': '',
                'returns': 0,
                'stock': row['stock']
            })

TRADES = []
trade_in_progress = False
holding_period = 14

for i in nifty_50_stocks:
    _df = yf.download(f"{i}",
                      period='1d',
                      start='2018-01-01',
                      end=(dt.now() + delta(1)).strftime('%Y-%m-%d'),
                      progress=False)
    _df.to_csv(f'data/{i}.csv')

    _df = add_signal_indicators(_df)

    _df['stock'] = i
    _df.reset_index().reset_index().apply(backtest_signals, axis=1)
    print(f'done performing backtesting for {i}')
    del _df
    trade_in_progress = False

pos = pd.DataFrame(TRADES).groupby('stock')['returns'].agg(['mean']).reset_index()
pos = pos.sort_values(by='mean', ascending=False).head(10)
ax = sb.barplot(x='stock', y='mean', data=pos)
ax.set_xticklabels(ax.get_xticklabels(), rotation=90)
plt.show()
