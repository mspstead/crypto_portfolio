import requests as req
import pandas as pd
import datetime
import matplotlib.pyplot as plt

trades_df = pd.read_csv('trades.csv')
trades_df['DateOfTrade']= pd.to_datetime(trades_df['DateOfTrade'])
trades_df = trades_df.sort_values(by='DateOfTrade')

comp_columns = ['StartDate','EndDate','CCY','Amount']
composition = pd.DataFrame(columns=comp_columns)

for trade in trades_df.itertuples():

    date_of_trade = getattr(trade,'DateOfTrade')
    ccy = getattr(trade,'CCY')
    amount = getattr(trade,'Amount')

    if ccy not in composition['CCY'].to_list():
        start_date = date_of_trade
        end_date = pd.datetime(2050,12,31)
        new_trade_df = pd.DataFrame({'StartDate':[start_date],'EndDate':[end_date],'CCY':[ccy],'Amount':[amount]})
        composition = pd.concat([composition,new_trade_df])

    else:
        current_ccy = (composition['EndDate'] == '2050-12-31') & (composition['CCY'] == ccy)
        if date_of_trade > composition.loc[current_ccy]['StartDate'][0]:

            new_amount = composition.loc[current_ccy]['Amount'][0] + amount
            if new_amount==0: #deletion
                composition.loc[current_ccy, 'EndDate'] = date_of_trade
            else:
                composition.loc[current_ccy,'EndDate'] = date_of_trade
                new_trade_df = pd.DataFrame({'StartDate': [date_of_trade], 'EndDate': [end_date], 'CCY': [ccy], 'Amount': [new_amount]})
                composition = pd.concat([composition, new_trade_df])


coin_ids = {'ETH':'ethereum','BTC':'bitcoin',
            'XRP':'ripple','ADA':'cardano','DOGE':'dogecoin',
            'BLZ':'bluzelle','SKL':'skale','SHIB':'shiba-inu'}
vs_currency = 'gbp'
prices_base_url = 'https://api.coingecko.com/api/v3/coins/'

coins_data = {}
for key,val in coin_ids.items():

    coin_start = composition[composition['CCY']==key]['StartDate'].min()
    coin_end = composition[composition['CCY']==key]['EndDate'].max()

    coin_start_epoch = '&from=' + str(coin_start.timestamp())
    coin_end_epoch = '&to=' + str(coin_end.timestamp())

    prices_url = prices_base_url + val + '/market_chart/range?vs_currency=' + vs_currency + coin_start_epoch + coin_end_epoch

    coin_prices = req.get(prices_url).json().get('prices')

    coin_price_dates={}
    for price in coin_prices:
        date = datetime.datetime.utcfromtimestamp(price[0]/1000).strftime('%Y-%m-%d')
        value = price[1]
        coin_price_dates[date] = value

    coins_data[key] = coin_price_dates

composition_start = composition['StartDate'].min()
curr_day = datetime.datetime.now()

def calculate_portfolio_value(day,composition):

    composition_on_day = composition[(composition['StartDate']<=day) & (composition['EndDate']>day)]

    mcap = 0
    for coin in composition_on_day['CCY'].values:
        prices = coins_data.get(coin)
        price_on_day = prices.get(day.strftime('%Y-%m-%d'))
        amount = composition_on_day[composition_on_day['CCY']==coin]['Amount'].values[0]

        mcap = mcap + (price_on_day*amount)

    return mcap

delta = curr_day - composition_start
portfolio_values = []
for i in range(0,delta.days):
    day = composition_start + datetime.timedelta(days=i)
    daily_portfolio_value = calculate_portfolio_value(day,composition)
    portfolio_values.append([day,daily_portfolio_value])

print(portfolio_values)
port_headers = ['Date','Value']
df = pd.DataFrame(columns=port_headers,data=portfolio_values)


