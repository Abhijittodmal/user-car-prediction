import joblib
import pandas as pd

from pathlib import Path

from flask import Flask, jsonify, render_template, request


app = Flask(__name__)

BASE_DIR = Path(__file__).resolve().parent
MODEL_PATH = BASE_DIR / "car_price_model.pkl"

FEATURES = [
    "Year",
    "Kilometers_Driven",
    "Engine_CC",
    "Mileage_Kmpl",
    "Brand",
    "Fuel_Type",
    "Transmission",
    "Owner"
]

NUMERIC_FIELDS = [
    "Year",
    "Kilometers_Driven",
    "Engine_CC",
    "Mileage_Kmpl"
]

CATEGORICAL_FIELDS = [
    "Brand",
    "Fuel_Type",
    "Transmission",
    "Owner"
]

if not MODEL_PATH.exists():
    raise FileNotFoundError(
        "Trained model not found. Run train_model.py first."
    )

saved_artifact = joblib.load(MODEL_PATH)
model = saved_artifact["model"]
target_column = saved_artifact["target_column"]


def recommend_car(predicted_price, asking_price):
    """
    Compare the asking price against the model's estimated value.

    The thresholds are illustrative decision rules.
    Both prices must use the same units.
    """

    if predicted_price <= 0:
        return {
            "recommendation": "REVIEW",
            "reason": (
                "The model predicted a non-positive price. "
                "Verify the model and its training data."
            )
        }

    difference = (asking_price - predicted_price) / predicted_price

    if difference <= -0.10:
        return {
            "recommendation": "BUY",
            "reason": (
                "The asking price is at least 10% below the "
                "estimated value. Inspect the car and verify "
                "its condition and documents before buying."
            )
        }

    if difference <= 0.05:
        return {
            "recommendation": "NEGOTIATE",
            "reason": (
                "The asking price is reasonably close to the "
                "estimated value. Consider negotiating."
            )
        }

    return {
        "recommendation": "DON'T BUY",
        "reason": (
            "The asking price is more than 5% above the "
            "estimated value. Consider negotiating or "
            "comparing similar cars."
        )
    }


@app.route("/")
def home():
    return render_template(
        "index.html",
        target_column=target_column
    )


@app.route("/predict", methods=["POST"])
def predict():
    try:
        data = request.get_json(silent=True)

        if not isinstance(data, dict):
            return jsonify({
                "error": "Please submit valid car details."
            }), 400

        required_fields = FEATURES + ["asking_price"]

        missing_fields = [
            field for field in required_fields
            if field not in data
        ]

        if missing_fields:
            return jsonify({
                "error": (
                    "Missing required fields: "
                    + ", ".join(missing_fields)
                )
            }), 400

        values = {}

        for field in NUMERIC_FIELDS:
            try:
                values[field] = float(data[field])
            except (TypeError, ValueError):
                return jsonify({
                    "error": f"{field} must be a valid number."
                }), 400

        asking_price = float(data["asking_price"])

        if not all(
            pd.notna(value)
            for value in list(values.values()) + [asking_price]
        ):
            return jsonify({
                "error": "Please enter valid numeric values."
            }), 400

        if values["Year"] < 1900 or values["Year"] > pd.Timestamp.now().year:
            return jsonify({
                "error": "Please enter a valid manufacturing year."
            }), 400

        if values["Kilometers_Driven"] < 0:
            return jsonify({
                "error": "Kilometers driven cannot be negative."
            }), 400

        if values["Engine_CC"] <= 0:
            return jsonify({
                "error": "Engine capacity must be greater than zero."
            }), 400

        if values["Mileage_Kmpl"] <= 0:
            return jsonify({
                "error": "Mileage must be greater than zero."
            }), 400

        if asking_price <= 0:
            return jsonify({
                "error": "Asking price must be greater than zero."
            }), 400

        for field in CATEGORICAL_FIELDS:
            value = data[field]

            if not isinstance(value, str) or not value.strip():
                return jsonify({
                    "error": f"Please provide a valid {field}."
                }), 400

            values[field] = value.strip()

        # Preserve the exact feature names expected by the model.
        input_data = pd.DataFrame([{
            feature: values[feature]
            for feature in FEATURES
        }])

        predicted_price = float(model.predict(input_data)[0])

        if not pd.notna(predicted_price):
            return jsonify({
                "error": "The model returned an invalid prediction."
            }), 500

        result = recommend_car(
            predicted_price,
            asking_price
        )

        return jsonify({
            "predicted_price": round(predicted_price, 2),
            "asking_price": round(asking_price, 2),
            "target_column": target_column,
            "recommendation": result["recommendation"],
            "reason": result["reason"]
        })

    except (TypeError, ValueError, OverflowError):
        return jsonify({
            "error": "Please check the entered values."
        }), 400

    except Exception:
        app.logger.exception("Prediction failed.")

        return jsonify({
            "error": (
                "Prediction failed. Please check the model "
                "and its input features."
            )
        }), 500


if __name__ == "__main__":
    app.run(debug=True)