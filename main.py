import yfinance as yf
import os
import requests
import json
from datetime import datetime

# GitHubのSecretsから読み込む設定
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
    r = requests.post(url, headers=headers, data=json.dumps(payload), timeout=15)
    print(f"LINE API Response: {r.status_code}")

def check_trade():
    try:
        # 1. 指標データの取得
        stock = yf.Ticker("1570.T").history(period="2mo")
        vix = yf.Ticker("^VIX").history(period="1d")['Close'].iloc[-1]
        # ドル円データを取得（前日比計算のため2日分）
        usdjpy_history = yf.Ticker("JPY=X").history(period="2d")['Close']
        
        current_price = stock['Close'].iloc[-1]
        ma25 = stock['Close'].rolling(window=25).mean().iloc[-1]
        
        # 2. 判定ロジック
        # 今日が第1金曜日か（米雇用統計回避）
        is_first_friday = (datetime.now().day <= 7 and datetime.now().weekday() == 4)
        
        # 円高判定（前日比で0.5円以上の円高になっていないか）
        # usdjpy_history[-1]が現在、[-2]が前日
        jpy_change = usdjpy_history.iloc[-1] - usdjpy_history.iloc[-2]
        is_safe_jpy = jpy_change > -0.5  # -0.5以下（例：-0.6）ならNG
        
        # 総合判定（すべての条件がTrueなら購入推奨）
        results = {
            "第1金曜回避": not is_first_friday,
            "VIX(20未満)": vix < 20,
            "25日線上": current_price > ma25,
            "円高警戒なし": is_safe_jpy
        }
        
        status = "🟢 【購入推奨】" if all(results.values()) else "🔴 【見送り推奨】"
        
        # 3. メッセージ作成
        msg = f"\n{status}\n"
        msg += f"第1金曜回避: {'OK' if not is_first_friday else 'NG'}\n"
        msg += f"VIX安定: {'OK' if vix < 20 else 'NG'}\n"
        msg += f"株価トレンド: {'OK' if current_price > ma25 else 'NG'}\n"
        msg += f"円高警戒: {'OK' if is_safe_jpy else 'NG'}\n"
        
        msg += f"\n--- 詳細データ ---\n"
        msg += f"日経レバ: {current_price:.0f}円\n"
        msg += f"VIX指数: {vix:.2f}\n"
        msg += f"ドル円: {usdjpy_history.iloc[-1]:.2f}\n"
        msg += f"円安/円高幅: {jpy_change:+.2f}円"
        
        send_line_push(msg)
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_trade()
