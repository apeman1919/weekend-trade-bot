import yfinance as yf
import os
import requests
from datetime import datetime

def send_line(message):
    token = os.getenv("LINE_TOKEN")
    url = "https://notify-api.line.me/api/notify"
    headers = {"Authorization": f"Bearer {token}"}
    payload = {"message": message}
    requests.post(url, headers=headers, data=payload)

def check_trade():
    nikkei_lev = yf.Ticker("1570.T").history(period="2mo")
    vix = yf.Ticker("^VIX").history(period="1d")['Close'].iloc[-1]
    usdjpy = yf.Ticker("JPY=X").history(period="2d")['Close']
    
    current_price = nikkei_lev['Close'].iloc[-1]
    ma25 = nikkei_lev['Close'].rolling(window=25).mean().iloc[-1]
    is_first_friday = (datetime.now().day <= 7 and datetime.now().weekday() == 4)
    jpy_change = usdjpy.iloc[-1] - usdjpy.iloc[-2]

    results = {
        "第一金曜回避": not is_first_friday,
        "VIX安定(20未満)": vix < 20,
        "25日線上(強気)": current_price > ma25,
        "円安傾向": jpy_change > -0.5
    }

    status = "🟢 【購入推奨】" if all(results.values()) else "🔴 【見送り推奨】"
    msg = f"\n{status}\n" + "\n".join([f"{k}: {'OK' if v else 'NG'}" for k, v in results.items()])
    msg += f"\n\n現在値: {current_price:.0f}円\nVIX: {vix:.2f}\nドル円: {usdjpy.iloc[-1]:.2f}"
    send_line(msg)

if __name__ == "__main__":
    check_trade()
