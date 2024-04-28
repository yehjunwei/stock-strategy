from FinMind.data import DataLoader

token = 'MY_API_TOKEN'

api = DataLoader()
api.login_by_token(api_token=token)

df = api.taiwan_stock_daily(
    stock_id='2330',
    start_date='2024-04-02',
    end_date='2024-04-28'
)

print(df.head())
