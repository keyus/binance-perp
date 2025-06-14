

import requests
import random
import os
import json
from tools import limit, interval_type

tg_main_channel = "https://t.me/c/2689649156/1"
tg_child_channel_url = "https://t.me/c/2689649156/4376"
# 替换为你的 chat_id
CHAT_ID = "-1002689649156"
BOT_TOKEN = "7609400654:AAGfvKRDyk_2b_lSsfg2khxXsylOoZ1xU0E"
url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

# 加载分析结果JSON文件
def load_json():
    with open("./data/result.json", "r",encoding='utf8') as f:
        try:
            data = list(json.load(f))
            if len(data) == 0:
                return None
            # 对data就行随机排序
            random.shuffle(data)
            return data[:3]
        except json.JSONDecodeError:
            print("JSON解码错误，可能是文件为空或格式不正确")
            return None
        

def send_telegram_message(text, chat_id=CHAT_ID):
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "HTML",
        "message_thread_id": 4376
    }
    try:
        resp = requests.post(url, data=payload)
        if resp.status_code == 200:
            print("消息已发送")
        else:
            print("发送失败:", resp.text)
    except Exception as e:
        print("发送异常:", e)
        
        
def run():
    data = load_json()
    if data is None:
        print("没有交易对可推送")
        return
    
    for item in data:
        diff_ratio = item.get('diff_ratio', 0)
        color_emoji = "🟢" if diff_ratio < 0 else "🔴"
        percent = round(diff_ratio * 100, 2)
        percent = f"+{percent}%🔺" if percent >= 0 else f"{percent}%"
        
        text = f"<b>[{item['symbol']}]</b>    {color_emoji} {item['direction']}          近{limit}{interval_type}\n" \
               f"最新价：{item['current_price']}    {percent}\n" \
               f"高：{item['high_price']}    低：{item['low_price']} \n"
        send_telegram_message(text)

# 示例用法
if __name__ == "__main__":
    send_telegram_message("你好，这是测试消息")