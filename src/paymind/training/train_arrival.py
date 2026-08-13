from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
import json

import pandas as pd

from catboost import CatBoostRegressor
from sklearn.metrics import (
    mean_absolute_error,
    mean_squared_error,
)

from paymind.features.builder import (
    build_arrival_features,
    get_categorical_features,
    get_feature_names,
)


DATA_DIR = Path("data/splits/arrival")
MODEL_DIR = Path("models/arrival")
REPORT_DIR = Path("data/reports")

TRAIN_PATH = DATA_DIR / "train.csv"
VALIDATION_PATH = DATA_DIR / "validation.csv"
TEST_PATH = DATA_DIR / "test.csv"

TARGET = "arrival_duration_minutes"


def load_dataset(
    path: Path,
) -> tuple[pd.DataFrame, pd.Series]:

    print(f"Loading: {path}")

    df = pd.read_csv(path)

    if TARGET not in df.columns:
        raise ValueError(
            f"{path} does not contain '{TARGET}'"
        )

    df = df[
        df[TARGET].notna()
        & (df[TARGET] >= 0)
    ].copy()

    feature_rows = [
        build_arrival_features(
            row.to_dict()
        )
        for _, row in df.iterrows()
    ]

    X = pd.DataFrame(feature_rows)

    y = df[TARGET].astype(float)

    return X, y


def quantile_coverage(
    y_true: pd.Series,
    predictions,
) -> float:

    return float(
        (y_true.to_numpy() <= predictions).mean()
    )


def train_quantile_model(
    *,
    alpha: float,
    X_train: pd.DataFrame,
    y_train: pd.Series,
    X_validation: pd.DataFrame,
    y_validation: pd.Series,
    categorical_features: list[str],
) -> CatBoostRegressor:

    model = CatBoostRegressor(
        loss_function=f"Quantile:alpha={alpha}",
        eval_metric=f"Quantile:alpha={alpha}",
        iterations=1500,
        learning_rate=0.04,
        depth=8,
        random_seed=42,
        l2_leaf_reg=5,
        random_strength=1,
        verbose=100,
        allow_writing_files=False,
        thread_count=-1,
    )

    model.fit(
        X_train,
        y_train,
        cat_features=categorical_features,
        eval_set=(
            X_validation,
            y_validation,
        ),
        early_stopping_rounds=150,
        use_best_model=True,
    )

    return model


def main() -> None:

    MODEL_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    REPORT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    print("=" * 70)
    print("PayMind Arrival Model V1")
    print("=" * 70)

    X_train, y_train = load_dataset(
        TRAIN_PATH
    )

    X_validation, y_validation = load_dataset(
        VALIDATION_PATH
    )

    X_test, y_test = load_dataset(
        TEST_PATH
    )

    feature_names = get_feature_names(
        "arrival"
    )

    categorical_features = (
        get_categorical_features(
            "arrival"
        )
    )

    print()
    print("Dataset sizes")
    print("-" * 50)
    print(f"Training:    {len(X_train):,}")
    print(f"Validation:  {len(X_validation):,}")
    print(f"Test:        {len(X_test):,}")

    print()
    print("Training P50 model...")

    p50_model = train_quantile_model(
        alpha=0.50,
        X_train=X_train,
        y_train=y_train,
        X_validation=X_validation,
        y_validation=y_validation,
        categorical_features=categorical_features,
    )

    print()
    print("Training P90 model...")

    p90_model = train_quantile_model(
        alpha=0.90,
        X_train=X_train,
        y_train=y_train,
        X_validation=X_validation,
        y_validation=y_validation,
        categorical_features=categorical_features,
    )

    print()
    print("Evaluating test data...")

    p50_pred = p50_model.predict(
        X_test
    )

    p90_pred = p90_model.predict(
        X_test
    )

    p50_mae = mean_absolute_error(
        y_test,
        p50_pred,
    )

    p50_rmse = mean_squared_error(
        y_test,
        p50_pred,
    ) ** 0.5

    p90_mae = mean_absolute_error(
        y_test,
        p90_pred,
    )

    p50_coverage = quantile_coverage(
        y_test,
        p50_pred,
    )

    p90_coverage = quantile_coverage(
        y_test,
        p90_pred,
    )

    # Safety check: P90 should not be below P50.
    ordering_violations = float(
        (p90_pred < p50_pred).mean()
    )

    print()
    print("=" * 70)
    print("ARRIVAL MODEL TEST RESULTS")
    print("=" * 70)

    print(
        f"P50 MAE:               "
        f"{p50_mae:.2f} min"
    )

    print(
        f"P50 RMSE:              "
        f"{p50_rmse:.2f} min"
    )

    print(
        f"P50 coverage:          "
        f"{p50_coverage:.4f}"
    )

    print(
        f"P90 MAE:               "
        f"{p90_mae:.2f} min"
    )

    print(
        f"P90 coverage:          "
        f"{p90_coverage:.4f}"
    )

    print(
        f"P90 < P50 violations:  "
        f"{ordering_violations:.4f}"
    )

    p50_path = (
        MODEL_DIR /
        "arrival_p50_v1.cbm"
    )

    p90_path = (
        MODEL_DIR /
        "arrival_p90_v1.cbm"
    )

    p50_model.save_model(
        str(p50_path)
    )

    p90_model.save_model(
        str(p90_path)
    )

    p50_importance = dict(
        zip(
            feature_names,
            p50_model.get_feature_importance(),
        )
    )

    p90_importance = dict(
        zip(
            feature_names,
            p90_model.get_feature_importance(),
        )
    )

    metadata = {
        "name":
            "paymind-arrival",

        "version":
            "1.0.0",

        "algorithm":
            "CatBoostRegressor",

        "objective":
            "Arrival time quantiles",

        "trained_at":
            datetime.now(
                timezone.utc
            ).isoformat(),

        "target":
            TARGET,

        "units":
            "minutes",

        "rows": {
            "train":
                len(X_train),

            "validation":
                len(X_validation),

            "test":
                len(X_test),
        },

        "features":
            feature_names,

        "categorical_features":
            categorical_features,

        "metrics": {
            "p50_mae_minutes":
                float(p50_mae),

            "p50_rmse_minutes":
                float(p50_rmse),

            "p50_coverage":
                float(p50_coverage),

            "p90_mae_minutes":
                float(p90_mae),

            "p90_coverage":
                float(p90_coverage),

            "p90_below_p50_rate":
                float(ordering_violations),
        },

        "feature_importance": {
            "p50":
                p50_importance,

            "p90":
                p90_importance,
        },
    }

    metadata_path = (
        MODEL_DIR /
        "metadata.json"
    )

    metadata_path.write_text(
        json.dumps(
            metadata,
            indent=2,
        ),
        encoding="utf-8",
    )

    report_path = (
        REPORT_DIR /
        "arrival_model_v1.txt"
    )

    report_path.write_text(
        f"""
PayMind Arrival Model V1
========================

P50 MAE
{p50_mae:.2f} minutes

P50 RMSE
{p50_rmse:.2f} minutes

P50 Coverage
{p50_coverage:.4f}

P90 MAE
{p90_mae:.2f} minutes

P90 Coverage
{p90_coverage:.4f}

P90 Below P50 Rate
{ordering_violations:.4f}

""",
        encoding="utf-8",
    )

    print()
    print("=" * 70)

    print(
        f"P50 model saved to: "
        f"{p50_path}"
    )

    print(
        f"P90 model saved to: "
        f"{p90_path}"
    )

    print(
        f"Metadata saved to: "
        f"{metadata_path}"
    )

    print(
        f"Report saved to: "
        f"{report_path}"
    )

    print("=" * 70)


if __name__ == "__main__":
    main()