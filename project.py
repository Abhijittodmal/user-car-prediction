import joblib
import numpy as np
import pandas as pd

from pathlib import Path

from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LinearRegression
from sklearn.metrics import (
    r2_score,
    mean_absolute_error,
    mean_squared_error
)
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler, OneHotEncoder


BASE_DIR = Path(__file__).resolve().parent
DATASET_PATH = BASE_DIR / "used_car_regression_dataset.csv"
MODEL_PATH = BASE_DIR / "car_price_model.pkl"

NUMERIC_FEATURES = [
    "Year",
    "Kilometers_Driven",
    "Engine_CC",
    "Mileage_Kmpl"
]

CATEGORICAL_FEATURES = [
    "Brand",
    "Fuel_Type",
    "Transmission",
    "Owner"
]

FEATURES = NUMERIC_FEATURES + CATEGORICAL_FEATURES


def main():
    data = pd.read_csv(DATASET_PATH)

    missing_features = [
        feature for feature in FEATURES
        if feature not in data.columns
    ]

    if missing_features:
        raise ValueError(
            f"Dataset is missing required features: {missing_features}"
        )

    if len(data.columns) < 2:
        raise ValueError("The dataset must contain features and a target.")

    # Preserve your original approach: the final column is the target.
    target_column = data.columns[-1]

    X = data[FEATURES].copy()
    y = pd.to_numeric(data[target_column], errors="coerce")

    valid_rows = y.notna()
    X = X.loc[valid_rows]
    y = y.loc[valid_rows]

    if len(X) < 5:
        raise ValueError("Not enough valid rows to train the model.")

    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=0.30,
        random_state=42
    )

    numerical_pipeline = Pipeline([
        ("imputer", SimpleImputer(strategy="mean")),
        ("scaler", StandardScaler())
    ])

    categorical_pipeline = Pipeline([
        (
            "imputer",
            SimpleImputer(strategy="most_frequent")
        ),
        (
            "onehot",
            OneHotEncoder(handle_unknown="ignore")
        )
    ])

    preprocessor = ColumnTransformer([
        ("num", numerical_pipeline, NUMERIC_FEATURES),
        ("cat", categorical_pipeline, CATEGORICAL_FEATURES)
    ])

    model = Pipeline([
        ("preprocessor", preprocessor),
        ("linear", LinearRegression())
    ])

    model.fit(X_train, y_train)

    predictions = model.predict(X_test)

    print("\nModel Evaluation")
    print("-" * 35)
    print(f"Target column: {target_column}")
    print(f"R² Score: {r2_score(y_test, predictions):.4f}")
    print(
        "MAE: "
        f"{mean_absolute_error(y_test, predictions):.4f}"
    )
    print(
        "RMSE: "
        f"{np.sqrt(mean_squared_error(y_test, predictions)):.4f}"
    )

    # Save the entire preprocessing and prediction pipeline.
    joblib.dump({
        "model": model,
        "features": FEATURES,
        "target_column": target_column
    }, MODEL_PATH)

    print(f"\nModel saved successfully: {MODEL_PATH}")


if __name__ == "__main__":
    main()