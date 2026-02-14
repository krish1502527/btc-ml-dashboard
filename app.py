from flask import Flask, render_template
import predictor
import pandas as pd

app = Flask(__name__)

@app.route("/")
def index():
    data = predictor.run_prediction()

    # Load history
    try:
        hist = pd.read_csv("prediction_history.csv").tail(50)
        labels = hist["timestamp"].tolist()
        probs = hist["probability"].tolist()
    except:
        labels, probs = [], []

    return render_template(
        "index.html",
        data=data,
        labels=labels,
        probs=probs
    )

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)

