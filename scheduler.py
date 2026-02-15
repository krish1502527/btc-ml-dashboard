from predictor import run_prediction
from database import engine
from sqlalchemy import text

def save_prediction():
    result = run_prediction()

    with engine.connect() as conn:
        conn.execute(text("""
            INSERT INTO predictions
            (date, regime, probability, confidence, action)
            VALUES (:date, :regime, :probability, :confidence, :action)
        """), {
            "date": result["date"],
            "regime": result["regime"],
            "probability": result["probability"],
            "confidence": result["confidence"],
            "action": result["action"]
        })
        conn.commit()

if __name__ == "__main__":
    save_prediction()
