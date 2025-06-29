from concurrent.futures import ThreadPoolExecutor
import requests
import json
import pandas as pd
import os
import shutil


# Binance Futures 
base_url = "https://fapi.binance.com"
# k线周期
interval = "1d"     
# 周期中文        
interval_type = '天'
# k线数量 7根k线
limit = 14                                
# 超涨比例限制 涨幅大于x倍
high_ratio = 1
# 超跌比例限制 跌幅大于x.
low_ratio = 0.65


# 获取交易对信息
def tiker():
    #如果存在tiker.json文件，则删除
    if os.path.exists("./data/tiker.json"):
        print("delete tiker json...")
        os.remove("./data/tiker.json")
        
    print("获取交易对信息,请稍等...")
    result = requests.get(f"{base_url}/fapi/v1/ticker/price")
    tiker = result.json()
    # 过滤掉不需要的交易对 btc,eth,bnb
    tiker = [
        t for t in tiker if not (t["symbol"] in ["BTC", "ETH", "BNB", "TRX"])
    ]
    with open("./data/tiker.json", "w") as f:
        print(len(tiker), "tiker found")
        json.dump(tiker, f, indent=4)


# 获取K线数据
def klines():
    try:
        with open("./data/tiker.json", "r") as f:
            tiker = json.load(f)
    except FileNotFoundError:
        print("Error: 文件未找到，请先运行tiker() 函数。")
        return

    # 强制删除旧的K线数据文件夹，创建新的文件夹
    if os.path.exists("./data/klines"):
        print("delete klines files")
        shutil.rmtree("./data/klines")
        os.makedirs("./data/klines", exist_ok=True)

    print("抓取k线...")

    def fetch_klines(
        symbol,
    ):
        try:
            result = requests.get(
                f"{base_url}/fapi/v1/klines?symbol={symbol}&interval={interval}&limit={limit}"
            )
            if result.status_code != 200:
                print(f"Error fetching {symbol} klines: {result.status_code}")
                return
            klines = result.json()
            if klines:
                klines = klines[1:]  # 去掉第一条数据，防止计入新币第一天的数据
                
            with open(f"./data/klines/{symbol}.json", "w") as f:
                json.dump(klines, f, indent=4)
        except Exception as e:
            print(f"Error fetching/saving {symbol} klines: {e}")
            os._exit(0)

    with ThreadPoolExecutor(max_workers=20) as executor:
        for t in tiker:
            symbol = t["symbol"]
            executor.submit(fetch_klines, symbol)


# 读取k线数据并分析超跌和超涨交易对
def read_klines():
    print("分析中...")
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
        current_price_time = t['time']
        file = f"./data/klines/{symbol}.json"
        try:
            if not os.path.exists(file):
                continue
            with open(file, "r") as f:
                data = json.load(f)
        except FileNotFoundError:
            print(f"Error: {symbol} 交易对 klines 数据文件不存在")
            break

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
        low_price_openTime = df.loc[df["low"] == low_price, "closeTime"].values[0]
        high_price = df["high"].max()
        high_price_openTime = df.loc[df["high"] == high_price, "closeTime"].values[0]
        # print('时间', low_price_openTime)
        
        # is_high_before_limit = current_price_time - high_price_openTime >=  1000 * 60 * 60 * 24 * 30 * limit_month
        # is_low_before_limit = current_price_time - low_price_openTime >=  1000 * 60 * 60 * 24 * 30 * limit_month
        
        # 把时间戳转换为可读时间格式
        times = pd.to_datetime(df["openTime"], unit="ms").to_string()
        symbol = symbol.replace("USDT", "").replace("BUSD", "")
        
        #涨幅大于5倍
        if current_price > low_price:
            diff = current_price - low_price
            diff_ratio = diff / low_price
            diff_ratio = round(diff_ratio, 2)
            
            if diff_ratio >= high_ratio:
                results.append(
                    {
                        "symbol": symbol,
                        "current_price": current_price,
                        "diff_ratio": diff_ratio,
                        "low_price": low_price,
                        "high_price": high_price,
                        "direction": "空",
                        "time": times,
                    }
                )
                
                
        # 跌幅小于50%
        if current_price < high_price:
            diff = high_price - current_price
            diff_ratio = diff / high_price
            diff_ratio = round(diff_ratio, 2)
            # print(f"{symbol} - {current_price}, {high_price} 价差： {diff}， 百分比：{diff_ratio * 100}%")
            if diff_ratio > low_ratio:
                results.append(
                    {
                        "symbol": symbol,
                        "current_price": current_price,
                        "diff_ratio": -diff_ratio,
                        "low_price": low_price,
                        "high_price": high_price,
                        "direction": "多",
                        "time": times,
                    }
                )

    with open("./data/result.json", "w", encoding="utf-8") as f:
        #对results进行排序，按diff_ratio降序排列
        results.sort(key=lambda x: x["diff_ratio"], reverse=True)
        json.dump(results, f, ensure_ascii=False, indent=4)
        print(f"晒选出来的交易对:  {len(results)} ")
