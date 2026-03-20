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
    try:
        r = requests.post(url, headers=headers, data=json.dumps(payload), timeout=15)
        print(f"LINE API Response: {r.status_code}")
    except Exception as e:
        print(f"LINE Send Error: {e}")

def check_trade():
    try:
        # 1. データの取得
        stock = yf.Ticker("1570.T").history(period="3mo")
        if stock.empty:
            send_line_push("⚠️本日は市場休場日のため、データが取得できませんでした。")
            return

        vix_data = yf.Ticker("^VIX").history(period="1d")
        vix = vix_data['Close'].iloc[-1] if not vix_data.empty else 0
        
        usdjpy_history = yf.Ticker("JPY=X").history(period="2d")['Close']
        
        current_price = stock['Close'].iloc[-1]
        ma25 = stock['Close'].rolling(window=25).mean().iloc[-1]
        
        # 2. 判定ロジック
        today_str = datetime.now().strftime("%Y-%m-%d")
        
        # 【2026年 米雇用統計 発表日リスト】(ズレる月を考慮)
        EMPLOYMENT_STATS_DATES = [
            "2026-04-03", "2026-05-08", "2026-06-05", 
            "2026-07-02", "2026-08-07", "2026-09-04",
            "2026-10-02", "2026-11-06", "2026-12-04"
        ]
        is_emp_day = today_str in EMPLOYMENT_STATS_DATES
        
        # 円高判定（前日比0.5円以上の円高か）
        jpy_change = usdjpy_history.iloc[-1] - usdjpy_history.iloc[-2]
        is_safe_jpy = jpy_change > -0.5
        
        results = {
            "雇用統計回避": not is_emp_day,
            "VIX安定(20未満)": vix < 20,
            "25日線上(強気)": current_price > ma25,
            "急激な円高なし": is_safe_jpy
        }
        
        status = "🟢 【購入推奨】" if all(results.values()) else "🔴 【見送り推奨】"
        
        # 3. メッセージ作成
        msg = f"\n{status}\n"
        msg += f"雇用統計回避: {'OK' if not is_emp_day else 'NG'}\n"
        msg += f"VIX安定: {'OK' if vix < 20 else 'NG'}\n"
        msg += f"株価トレンド: {'OK' if current_price > ma25 else 'NG'}\n"
        msg += f"円高警戒: {'OK' if is_safe_jpy else 'NG'}\n"
        
        # 新ルール（日経レバ12株）に基づいた情報
        total_cost = current_price * 12
        msg += f"\n--- 運用状況(12株固定) ---\n"
        msg += f"現在株価: {current_price:.0f}円\n"
        msg += f"必要資金: {total_cost:,.0f}円\n"
        msg += f"VIX指数: {vix:.2f}\n"
        msg += f"ドル円: {usdjpy_history.iloc[-1]:.2f} ({jpy_change:+.2f})\n"
        
        if all(results.values()):
            msg += "\n💡 本日大引けで12株購入、月曜始値で決済の条件を満たしています。"
        else:
            msg += "\n🚫 条件を満たしていないため、今週は見送りを推奨します。"
            
        send_line_push(msg)
        
    except Exception as e:
        error_msg = f"❌ システムエラーが発生しました:\n{str(e)}"
        print(error_msg)
        send_line_push(error_msg)

if __name__ == "__main__":
    check_trade()
