from config import api_key, api_secret
from concurrent.futures import ThreadPoolExecutor
import requests
import json
import pandas as pd
import os

base_url = "https://fapi.binance.com"
 # 超跌比例
low_ratio = 0.7
high_ratio = 3.0

# 获取交易对信息
def tiker():
    if os.path.exists("./data/tiker.json"):
        return 
    print("获取交易对信息,请稍等...")
    result = requests.get(f'{base_url}/fapi/v1/ticker/price')
    tiker = result.json()
    with open("./data/tiker.json", "w") as f:
        print(len(tiker), "tiker found")
        json.dump(tiker, f, indent=4)
   

# 获取K线数据月线
def klines():
    try:
        with open("./data/tiker.json", "r") as f:
            tiker = json.load(f)
    except FileNotFoundError:
        print("Error: 文件未找到，请先运行tiker() 函数。")
        return

    print('抓取k线数据,请稍等...')
    def fetch_klines(
        symbol,
    ):
        try:
            result = requests.get(f'{base_url}/fapi/v1/klines?symbol={symbol}&interval=1M&limit=4')
            klines = result.json()
            with open(f"./data/klines/{symbol}.json", "w") as f:
                json.dump(klines, f, indent=4)
        except Exception as e:
            print(f"Error fetching/saving {symbol} klines: {e}")
            os._exit(0)

    with ThreadPoolExecutor(max_workers=20) as executor:
        for t in tiker:
            symbol = t["symbol"]
            executor.submit(fetch_klines, symbol)


# 读取交易对月线json文件
def read_klines():
    print("开始读取交易对月线数据,分析超跌和超涨交易对")
    try:
        with open("./data/tiker.json", "r") as f:
            tiker = json.load(f)
    except FileNotFoundError:
        print("Error: 文件未找到，请先运行tiker() 函数。")
        return

    results = []
    for t in tiker:
        symbol = t["symbol"]
        current_price = float(t.get("price", 0.0))
        try:
            with open(f"./data/klines/{symbol}.json", "r") as f:
                data = json.load(f)
        except FileNotFoundError:
            print(f"Error: {symbol} 交易对 klines 数据文件不存在")
            return None

        df = pd.DataFrame(
            data,
            columns=[
                "openTime",
                "open",
                "high",
                "low",
                "close",
                "volume",
                "closeTime",
                "qav",
                "numTrades",
                "takerBuyBaseQty",
                "takerBuyQuoteQty",
                "ignore",
            ],
        )

        df[["high", "low", "close"]] = df[["high", "low", "close"]].astype(float)
        low_price = df["low"].min()
        high_price = df["high"].max()
        # 把时间戳转换为可读时间格式
        times = pd.to_datetime(df["openTime"], unit="ms").to_string()

        if current_price > low_price:
            diff_ratio = current_price / low_price
            if diff_ratio >= high_ratio:
                results.append(
                    {
                        "symbol": symbol,
                        "current_price": current_price,
                        "type": f"涨{diff_ratio}倍以上",
                        "time": times,
                        "low_price": low_price,
                        "high_price": high_price,
                    }
                )

        if current_price < high_price:
            diff = high_price - current_price
            diff_ratio = diff / high_price
            # print(f"{symbol} - {current_price}, {high_price} 价差： {diff}， 百分比：{diff_ratio * 100}%")
            if diff/ high_price >= low_ratio:
                results.append(
                    {
                        "symbol": symbol,
                        "current_price": current_price,
                        "type": f"跌>{diff_ratio * 100}%",
                        "time": times,
                        "low_price": low_price,
                        "high_price": high_price,
                    }
                )

    with open("./data/result.json", "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=4)
        print(f"晒选出来的交易对:  {len(results)} ")
