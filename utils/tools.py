from config import api_key, api_secret
from binance.cm_futures import CMFutures
from concurrent.futures import ThreadPoolExecutor
import json
import pandas as pd
 
# 创建客户端 
def get_client():
    cm_futures_client = CMFutures(key=api_key, secret=api_secret)
    return cm_futures_client

# 下载交易所信息
def download_exchange_info():
    cm_futures_client = get_client()
    exchange_info = cm_futures_client.exchange_info()
    
    with open('./data/exchange_info.json', 'w') as f:
        symbols = exchange_info.get('symbols', [])
        symbols = list(
            filter(lambda x: x.get('symbol').endswith('_PERP') and x.get('contractStatus') == 'TRADING', symbols)
        )
        print(len(symbols), "symbols found")
        # 遍历symbols 只保留 symbol,字段
        symbols = [{'symbol': symbol['symbol']} for symbol in symbols]
        json.dump(symbols, f, indent=4)
    return exchange_info

# 获取交易对信息
def tiker():
    cm_futures_client = get_client()
    tiker = cm_futures_client.ticker_price()
    with open('./data/tiker.json', 'w') as f:
        tiker = list(
            filter(lambda x: x.get('symbol').endswith('_PERP'), tiker)
        )
        print(len(tiker), "tiker found")
        json.dump(tiker, f, indent=4)
        

# 获取K线数据 月线
def klines():
    cm_futures_client = get_client()
    #读取 tiker.json文件
    # with open('./data/tiker.json', 'r') as f:
    #     tiker = json.load(f)
        
    # for t in tiker:
    #     symbol = t['symbol']
    #     klines = cm_futures_client.klines(symbol=symbol, interval='1m', limit=4)
    #     with open(f'./data/klines/{symbol}.json', 'w') as f:
    #         json.dump(klines, f, indent=4)
    #     print(f"{symbol} klines saved")
        
        
    try:
        with open('./data/tiker.json', 'r') as f:
            tiker = json.load(f)
    except FileNotFoundError:
        print("Error: 文件未找到，请先运行tiker() 函数。")
        return
    
    def fetch_klines(symbol, ):
        try:
            result = cm_futures_client.klines(symbol=symbol, interval='1m', limit=4)
            with open(f'./data/klines/{symbol}.json', 'w') as f:
                json.dump(result, f, indent=4)
                print(f"{symbol} klines saved")
        except Exception as e:
            print(f"Error fetching/saving {symbol} klines: {e}")
            
    with ThreadPoolExecutor(max_workers=10) as executor: 
        for t in tiker:
            symbol = t['symbol']
            executor.submit(fetch_klines, symbol)
    
# 读取交易对月线json文件
def read_klines():
    try:
        with open('./data/tiker.json', 'r') as f:
            tiker = json.load(f)
    except FileNotFoundError:
        print("Error: 文件未找到，请先运行tiker() 函数。")
        return
    
    results = [] 
    for t in tiker:
        symbol = t['symbol']
        try:
            print(f"Processing {symbol}...")
            with open(f'./data/klines/{symbol}.json', 'r') as f:
                data = json.load(f)
        except FileNotFoundError:
            print(f"Error: {symbol} 交易对 klines 数据文件不存在")
            return None      
          
        df = pd.DataFrame(data, columns=[
            'openTime','open','high','low','close','volume',
            'closeTime','qav','numTrades','takerBuyBaseQty',
            'takerBuyQuoteQty','ignore'
        ])

        df[['high','low','close']] = df[['high','low','close']].astype(float)
        low_price = df['low'].min()
        high_price = df['high'].max()
        current_price = df['close'].iloc[-1]

        if current_price / low_price >= 3:
            results.append({
                'symbol': symbol,
                'type': '涨 ≥ 3 倍',
                'low': low_price,
                'current': current_price,
                'ratio': round(current_price / low_price, 2)
            })
        elif (high_price - current_price) / high_price >= 0.7:
            results.append({
                'symbol': symbol,
                'type': '跌 ≥ 70%',
                'high': high_price,
                'current': current_price,
                'ratio': round((high_price - current_price) / high_price * 100, 2)
            })
            
        
    with open('./data/result.json', 'w') as f:
        json.dump(results, f, indent=4)
        print(f"Results saved to ./data/result.json with {len(results)} entries")