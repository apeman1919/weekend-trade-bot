import yfinance as yf
import os
import requests
import json
from datetime import datetime

# GitHubのSecretsから読み込みます
# ※設定方法は下で説明します
LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
USER_ID = os.getenv("USER_ID")

def send_line_push(message):
    url = "https://api.line.me/v2/bot/message/push"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {LINE_CHANNEL_ACCESS_TOKEN}"
    }
    payload = {
        "to": USER_ID,
        "messages": [{"type": "text", "text": message}]
    }
    # 2026年版の最新APIへ送信
    requests.post(url, headers=headers, data=json.dumps(payload), timeout=15)

def check_trade():
    try:
        # 指標データの取得
        stock = yf.Ticker("1570.T").history(period="2mo")
        vix = yf.Ticker("^VIX").history(period="1d")['Close'].iloc[-1]
        usdjpy = yf.Ticker("JPY=X").history(period="2d")['Close']
        
        current_price = stock['Close'].iloc[-1]
        ma25 = stock['Close'].rolling(window=25).mean().iloc[-1]
        
        # 今日が「第1金曜日」かどうか（3/6はNG判定になります）
        is_first_friday = (datetime.now().day <= 7 and datetime.now().weekday() == 4)
        
        status = "🟢 【購入推奨】" if (not is_first_friday and vix < 20 and current_price > ma25) else "🔴 【見送り推奨】"
        
        msg = f"\n{status}\n"
        msg += f"第1金曜回避: {'OK' if not is_first_friday else 'NG'}\n"
        msg += f"VIX(20未満): {'OK' if vix < 20 else 'NG'}\n"
        msg += f"25日線上: {'OK' if current_price > ma25 else 'NG'}\n"
        msg += f"\n日経レバ: {current_price:.0f}円\nドル円: {usdjpy.iloc[-1]:.2f}"
        
        send_line_push(msg)
    except Exception as e:
        send_line_push(f"エラー発生: {str(e)}")

if __name__ == "__main__":
    check_trade()
