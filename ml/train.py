from __future__ import annotations

import argparse
from pathlib import Path

import joblib
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.metrics import classification_report
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.linear_model import LogisticRegression


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
    test_size = 0.2
    if stratify is not None and len(y) < max(10, 2 * y.nunique()):
        test_size = 0.5

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=test_size, random_state=42, stratify=stratify
    )

    pipe = build_pipeline(X_train)
    pipe.fit(X_train, y_train)

    y_pred = pipe.predict(X_test)
    print(classification_report(y_test, y_pred))

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(pipe, out_path)
    print(f"Saved model to: {out_path.resolve()}")


if __name__ == "__main__":
    main()

