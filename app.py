from flask import Flask, render_template
from sqlalchemy import text
from database import engine, create_table
from scheduler import save_prediction

app = Flask(__name__)

# Create table on startup (safe to run multiple times)
create_table()


@app.route("/")
def index():
    """
    Homepage: Just reads latest prediction from database.
    No heavy computation here.
    """

    with engine.connect() as conn:
        result = conn.execute(text("""
            SELECT date, regime, probability, confidence, action
            FROM predictions
            ORDER BY created_at DESC
            LIMIT 1
        """)).fetchone()

    if result:
        # Color logic
        if result.confidence == "High":
            color = "#22c55e"   # green
        elif result.confidence == "Moderate":
            color = "#facc15"   # yellow
        else:
            color = "#ef4444"   # red

        data = {
            "date": str(result.date),
            "regime": result.regime,
            "probability": result.probability,
            "confidence": result.confidence,
            "action": result.action,
            "color": color,
            "window": "",
            "explanations": []
        }

    else:
        # If no prediction yet in database
        data = {
            "date": "N/A",
            "regime": "No Data Yet",
            "probability": 0,
            "confidence": "N/A",
            "action": "Prediction not generated yet",
            "color": "#ef4444",
            "window": "",
            "explanations": []
        }

    return render_template(
        "index.html",
        data=data,
        labels=[],
        probs=[]
    )


@app.route("/run-job")
def run_job():
    """
    This endpoint triggers prediction manually.
    UptimeRobot will call this once daily.
    """
    save_prediction()
    return "Prediction saved successfully!"


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
