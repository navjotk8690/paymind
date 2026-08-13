from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
import json

import pandas as pd

from catboost import CatBoostClassifier
from sklearn.metrics import (
    accuracy_score,
    average_precision_score,
    brier_score_loss,
    classification_report,
    confusion_matrix,
    log_loss,
    roc_auc_score,
)

from paymind.features.builder import (
    build_success_features,
    get_categorical_features,
    get_feature_names,
)


DATA_DIR = Path("data/splits/success")
MODEL_DIR = Path("models/success")
REPORT_DIR = Path("data/reports")

TRAIN_PATH = DATA_DIR / "train.csv"
VALIDATION_PATH = DATA_DIR / "validation.csv"
TEST_PATH = DATA_DIR / "test.csv"


def load_dataset(
    path: Path,
) -> tuple[pd.DataFrame, pd.Series]:

    print(f"Loading: {path}")

    df = pd.read_csv(path)

    if "success" not in df.columns:
        raise ValueError(
            f"{path} does not contain 'success'"
        )

    df = df[
        df["success"].isin([0, 1])
    ].copy()

    feature_rows = [
        build_success_features(
            row.to_dict()
        )
        for _, row in df.iterrows()
    ]

    X = pd.DataFrame(feature_rows)

    y = (
        df["success"]
        .astype(int)
    )

    return X, y


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
    print("PayMind Success Model V1")
    print("=" * 70)

    # --------------------------------------------------
    # Load data
    # --------------------------------------------------

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
        "success"
    )

    categorical_features = (
        get_categorical_features(
            "success"
        )
    )

    print()
    print("Dataset sizes")
    print("-" * 50)

    print(
        f"Training:    {len(X_train):,}"
    )

    print(
        f"Validation:  "
        f"{len(X_validation):,}"
    )

    print(
        f"Test:        {len(X_test):,}"
    )

    print()

    print(
        f"Training success rate: "
        f"{y_train.mean():.2%}"
    )

    print(
        f"Validation success rate: "
        f"{y_validation.mean():.2%}"
    )

    print(
        f"Test success rate: "
        f"{y_test.mean():.2%}"
    )

    print()
    print("Features")

    for feature in feature_names:
        print(f"  {feature}")

    # --------------------------------------------------
    # Train
    # --------------------------------------------------

    print()
    print("Training CatBoost...")
    print("-" * 50)

    model = CatBoostClassifier(
        loss_function="Logloss",
        eval_metric="AUC",

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

        cat_features=
            categorical_features,

        eval_set=(
            X_validation,
            y_validation,
        ),

        early_stopping_rounds=150,

        use_best_model=True,
    )

    # --------------------------------------------------
    # Predict
    # --------------------------------------------------

    print()
    print("Evaluating test data...")
    print("-" * 50)

    probabilities = (
        model.predict_proba(
            X_test
        )[:, 1]
    )

    predictions = (
        probabilities >= 0.50
    ).astype(int)

    # --------------------------------------------------
    # Metrics
    # --------------------------------------------------

    roc_auc = roc_auc_score(
        y_test,
        probabilities,
    )

    pr_auc = average_precision_score(
        y_test,
        probabilities,
    )

    loss = log_loss(
        y_test,
        probabilities,
    )

    brier = brier_score_loss(
        y_test,
        probabilities,
    )

    accuracy = accuracy_score(
        y_test,
        predictions,
    )

    report_text = (
        classification_report(
            y_test,
            predictions,
            digits=4,
            zero_division=0,
        )
    )

    matrix = confusion_matrix(
        y_test,
        predictions,
    )

    # --------------------------------------------------
    # Display
    # --------------------------------------------------

    print()
    print("=" * 70)
    print("SUCCESS MODEL TEST RESULTS")
    print("=" * 70)

    print(
        f"ROC-AUC:      "
        f"{roc_auc:.4f}"
    )

    print(
        f"PR-AUC:       "
        f"{pr_auc:.4f}"
    )

    print(
        f"Log Loss:     "
        f"{loss:.4f}"
    )

    print(
        f"Brier Score:  "
        f"{brier:.4f}"
    )

    print(
        f"Accuracy:     "
        f"{accuracy:.4f}"
    )

    print()

    print(
        "Confusion Matrix"
    )

    print(matrix)

    print()

    print(
        "Classification Report"
    )

    print(report_text)

    # --------------------------------------------------
    # Feature importance
    # --------------------------------------------------

    importance_values = (
        model.get_feature_importance()
    )

    feature_importance = sorted(
        zip(
            feature_names,
            importance_values,
        ),
        key=lambda item: item[1],
        reverse=True,
    )

    print()
    print("Feature Importance")
    print("-" * 50)

    for feature, importance in (
        feature_importance
    ):
        print(
            f"{feature:30}"
            f"{importance:10.4f}"
        )

    # --------------------------------------------------
    # Save model
    # --------------------------------------------------

    model_path = (
        MODEL_DIR /
        "success_v1.cbm"
    )

    model.save_model(
        str(model_path)
    )

    # --------------------------------------------------
    # Metadata
    # --------------------------------------------------

    metadata = {
        "name":
            "paymind-success",

        "version":
            "1.0.0",

        "algorithm":
            "CatBoostClassifier",

        "objective":
            "Binary success probability",

        "trained_at":
            datetime.now(
                timezone.utc
            ).isoformat(),

        "dataset": {
            "train":
                str(TRAIN_PATH),

            "validation":
                str(VALIDATION_PATH),

            "test":
                str(TEST_PATH),
        },

        "rows": {
            "train":
                len(X_train),

            "validation":
                len(X_validation),

            "test":
                len(X_test),
        },

        "success_rates": {
            "train":
                float(
                    y_train.mean()
                ),

            "validation":
                float(
                    y_validation.mean()
                ),

            "test":
                float(
                    y_test.mean()
                ),
        },

        "features":
            feature_names,

        "categorical_features":
            categorical_features,

        "metrics": {
            "roc_auc":
                float(roc_auc),

            "pr_auc":
                float(pr_auc),

            "log_loss":
                float(loss),

            "brier_score":
                float(brier),

            "accuracy":
                float(accuracy),
        },

        "feature_importance": {
            feature:
                float(importance)

            for (
                feature,
                importance
            ) in feature_importance
        },

        "threshold":
            0.50,
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

    # --------------------------------------------------
    # Human-readable report
    # --------------------------------------------------

    report_path = (
        REPORT_DIR /
        "success_model_v1.txt"
    )

    report_contents = f"""
PayMind Success Model V1
========================

ROC-AUC
{roc_auc:.4f}

PR-AUC
{pr_auc:.4f}

Log Loss
{loss:.4f}

Brier Score
{brier:.4f}

Accuracy
{accuracy:.4f}


Confusion Matrix
----------------

{matrix}


Classification Report
---------------------

{report_text}


Feature Importance
------------------

"""

    for (
        feature,
        importance
    ) in feature_importance:

        report_contents += (
            f"{feature:30}"
            f"{importance:10.4f}\n"
        )

    report_path.write_text(
        report_contents,
        encoding="utf-8",
    )

    # --------------------------------------------------
    # Done
    # --------------------------------------------------

    print()
    print("=" * 70)

    print(
        f"Model saved to: "
        f"{model_path}"
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