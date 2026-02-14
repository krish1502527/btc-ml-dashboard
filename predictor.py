import pandas as pd
import joblib
import ta
import ccxt
import os
from datetime import datetime, timedelta


# ===============================
# PATHS
# ===============================
#CSV_PATH = r"C:\Users\krish\OneDrive\Desktop\BITCOIN FINAL FOLDER FOR PREDICTION!\testing!.csv"
#MODEL_PATH = r"C:\Users\krish\OneDrive\Desktop\BITCOIN FINAL FOLDER FOR PREDICTION!\btc_ml_oos_model_by_krish.pkl"
#HISTORY_PATH = r"C:\Users\krish\OneDrive\Desktop\BITCOIN FINAL FOLDER FOR PREDICTION!\prediction_history.csv"
CSV_PATH = "testing!.csv"
MODEL_PATH = "btc_ml_oos_model_by_krish.pkl"
HISTORY_PATH = "prediction_history.csv"

SYMBOL = "BTC/USDT"
TIMEFRAME = "1d"


# ===============================
# SAVE PREDICTION HISTORY
# ===============================
def save_history(result):
    row = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "date": result["date"],
        "regime": result["regime"],
        "probability": result["probability"],
        "confidence": result["confidence"],
        "action": result["action"]
    }

    df = pd.DataFrame([row])

    if os.path.exists(HISTORY_PATH):
        df.to_csv(HISTORY_PATH, mode="a", header=False, index=False)
    else:
        df.to_csv(HISTORY_PATH, index=False)


# ===============================
# MAIN PREDICTION FUNCTION
# ===============================
def run_prediction():
    exchange = ccxt.binance({"enableRateLimit": True})

    # -------------------------------
    # Load existing BTC CSV
    # -------------------------------
    df_existing = pd.read_csv(CSV_PATH)
    df_existing["Date"] = pd.to_datetime(df_existing["Date"], dayfirst=True)

    last_date = df_existing["Date"].max()
    since = int((last_date + timedelta(days=1)).timestamp() * 1000)

    # -------------------------------
    # Fetch new candles
    # -------------------------------
    try:
        ohlcv = exchange.fetch_ohlcv(SYMBOL, TIMEFRAME, since=since, limit=1000)
    except Exception:
        ohlcv = []

    if ohlcv:
        df_new = pd.DataFrame(
            ohlcv,
            columns=["Timestamp", "Open", "High", "Low", "Close", "Volume"]
        )

        df_new["Date"] = pd.to_datetime(df_new["Timestamp"], unit="ms")
        df_new["Date"] = df_new["Date"].dt.strftime("%d-%m-%Y")
        df_new = df_new[["Date", "Open", "High", "Low", "Close", "Volume"]]

        df_existing["Date"] = df_existing["Date"].dt.strftime("%d-%m-%Y")
        df_existing = pd.concat([df_existing, df_new], ignore_index=True)
        df_existing.drop_duplicates(subset=["Date"], keep="last", inplace=True)

        df_existing.to_csv(CSV_PATH, index=False)

    # -------------------------------
    # Reload clean dataset
    # -------------------------------
    btc = pd.read_csv(CSV_PATH)
    btc["Date"] = pd.to_datetime(btc["Date"], dayfirst=True)
    btc.set_index("Date", inplace=True)
    btc.sort_index(inplace=True)

    for col in ["Open", "High", "Low", "Close", "Volume"]:
        btc[col] = pd.to_numeric(btc[col], errors="coerce")

    btc.dropna(inplace=True)

    # ===============================
    # FEATURE ENGINEERING
    # ===============================
    btc["ret_1d"] = btc["Close"].pct_change()
    btc["ret_5d"] = btc["Close"].pct_change(5)
    btc["ret_20d"] = btc["Close"].pct_change(20)

    btc["vol_10d"] = btc["ret_1d"].rolling(10).std()
    btc["vol_30d"] = btc["ret_1d"].rolling(30).std()

    btc["rsi"] = ta.momentum.RSIIndicator(btc["Close"], 14).rsi()

    btc["ema_fast"] = ta.trend.EMAIndicator(btc["Close"], 20).ema_indicator()
    btc["ema_slow"] = ta.trend.EMAIndicator(btc["Close"], 50).ema_indicator()

    btc["trend"] = (btc["ema_fast"] - btc["ema_slow"]) / btc["ema_slow"]
    btc["price_vs_ema"] = (btc["Close"] - btc["ema_slow"]) / btc["ema_slow"]
    btc["bull_regime"] = (btc["Close"] > btc["ema_slow"]).astype(int)

    btc.dropna(inplace=True)

    FEATURES = [
        "ret_5d",
        "ret_20d",
        "vol_10d",
        "vol_30d",
        "rsi",
        "trend",
        "price_vs_ema",
        "bull_regime",
    ]

    # ===============================
    # MODEL PREDICTION
    # ===============================
    model = joblib.load(MODEL_PATH)

    latest = btc.iloc[-1:][FEATURES]
    prob = model.predict_proba(latest)[0, 1]

    regime = "Bullish" if latest["bull_regime"].iloc[0] == 1 else "Bearish"

    # Confidence labels
    if prob >= 0.70:
        confidence = "High"
        color = "#22c55e"   # green
    elif prob >= 0.55:
        confidence = "Moderate"
        color = "#facc15"   # yellow
    else:
        confidence = "Low"
        color = "#ef4444"   # red

    if prob >= 0.65 and regime == "Bullish":
        action = "HOLD / ENTER LONG"
    else:
        action = "STAY OUT"

    today = latest.index[0].date()
    start = today + timedelta(days=1)
    end = start + timedelta(days=4)

    # ===============================
    # EXPLANATION LOGIC
    # ===============================
    explanations = []

    rsi_val = btc["rsi"].iloc[-1]
    trend_val = btc["trend"].iloc[-1]
    vol10 = btc["vol_10d"].iloc[-1]
    vol30 = btc["vol_30d"].iloc[-1]

    if trend_val > 0:
        explanations.append("Price is trading above the long-term EMA, indicating bullish trend strength.")
    else:
        explanations.append("Price is trading below the long-term EMA, indicating bearish pressure.")

    if rsi_val > 70:
        explanations.append("RSI indicates overbought conditions.")
    elif rsi_val < 30:
        explanations.append("RSI indicates oversold conditions.")
    else:
        explanations.append("RSI is in a neutral range.")

    if vol10 > vol30:
        explanations.append("Short-term volatility is higher than long-term volatility.")
    else:
        explanations.append("Market volatility is relatively stable.")

    if prob >= 0.7:
        explanations.append("Model confidence is high, suggesting stronger upward probability.")
    elif prob >= 0.55:
        explanations.append("Model confidence is moderate, indicating uncertainty.")
    else:
        explanations.append("Model confidence is low, showing weak upside probability.")

    # ===============================
    # FINAL OUTPUT
    # ===============================
    result = {
        "date": str(today),
        "regime": regime,
        "probability": round(prob * 100, 2),
        "confidence": confidence,
        "action": action,
        "color": color,
        "window": f"{start} → {end}",
        "explanations": explanations,
    }

    save_history(result)

    return result
