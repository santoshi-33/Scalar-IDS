from __future__ import annotations

import argparse
from pathlib import Path

import joblib
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.metrics import confusion_matrix
from sklearn.metrics import classification_report
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.linear_model import LogisticRegression
import json


def build_pipeline(X: pd.DataFrame) -> Pipeline:
    numeric_cols = X.select_dtypes(include=["number", "bool"]).columns.tolist()
    categorical_cols = [c for c in X.columns if c not in numeric_cols]

    numeric_pipe = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="median")),
            ("scaler", StandardScaler()),
        ]
    )

    categorical_pipe = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="most_frequent")),
            ("onehot", OneHotEncoder(handle_unknown="ignore")),
        ]
    )

    pre = ColumnTransformer(
        transformers=[
            ("num", numeric_pipe, numeric_cols),
            ("cat", categorical_pipe, categorical_cols),
        ],
        remainder="drop",
    )

    clf = LogisticRegression(max_iter=1500)

    return Pipeline(steps=[("preprocess", pre), ("model", clf)])


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", required=True, help="Path to CSV dataset")
    parser.add_argument(
        "--label-col",
        default="label",
        help="Name of label column (default: label)",
    )
    parser.add_argument(
        "--out",
        default=str(Path("backend/app/artifacts/ids_model.joblib")),
        help="Output model path",
    )
    parser.add_argument(
        "--metrics-out",
        default=str(Path("backend/app/artifacts/metrics.json")),
        help="Output metrics JSON path",
    )
    args = parser.parse_args()

    data_path = Path(args.data)
    if not data_path.exists():
        raise SystemExit(f"Dataset not found: {data_path}")

    df = pd.read_csv(data_path)
    if args.label_col not in df.columns:
        raise SystemExit(f"Label column '{args.label_col}' not found. Columns: {list(df.columns)[:20]}...")

    y = df[args.label_col].astype(str)
    X = df.drop(columns=[args.label_col])

    # For tiny demo datasets, ensure the test split has at least one sample per class.
    stratify = y if y.nunique() > 1 else None
    if stratify is not None:
        try:
            # Stratified split requires at least 2 samples per class.
            if y.value_counts().min() < 2:
                stratify = None
        except Exception:
            stratify = None
    test_size = 0.2
    if stratify is not None and len(y) < max(10, 2 * y.nunique()):
        test_size = 0.5

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=test_size, random_state=42, stratify=stratify
    )

    pipe = build_pipeline(X_train)
    pipe.fit(X_train, y_train)

    y_pred = pipe.predict(X_test)
    report_dict = classification_report(y_test, y_pred, output_dict=True, zero_division=0)
    print(classification_report(y_test, y_pred, zero_division=0))

    labels = sorted(set(y_test.astype(str).tolist()) | set(pd.Series(y_pred).astype(str).tolist()))
    cm = confusion_matrix(y_test, y_pred, labels=labels)

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(pipe, out_path)
    print(f"Saved model to: {out_path.resolve()}")

    metrics_path = Path(args.metrics_out)
    metrics_path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "labels": labels,
        "confusion_matrix": cm.tolist(),
        "classification_report": report_dict,
        "n_train": int(len(X_train)),
        "n_test": int(len(X_test)),
    }
    metrics_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(f"Saved metrics to: {metrics_path.resolve()}")


if __name__ == "__main__":
    main()

