from __future__ import annotations

from pathlib import Path
import json
from datetime import datetime, timezone

import pandas as pd
from catboost import CatBoostClassifier
from sklearn.metrics import accuracy_score, log_loss, classification_report

from paymind.features.builder import (
    build_payment_method_features,
    get_categorical_features,
    get_feature_names,
)


DATA_DIR = Path("data/splits/payment_method")
MODEL_DIR = Path("models/payment_method")
REPORT_DIR = Path("data/reports")


TRAIN_PATH = DATA_DIR / "train.csv"
VALIDATION_PATH = DATA_DIR / "validation_model.csv"
TEST_PATH = DATA_DIR / "test_model.csv"


def load_features(path: Path):
    df = pd.read_csv(path)

    rows = [
        build_payment_method_features(
            row.to_dict()
        )
        for _, row in df.iterrows()
    ]

    X = pd.DataFrame(rows)

    y = (
        df["payment_type"]
        .astype(str)
        .str.strip()
        .str.lower()
    )

    return X, y


def top_k_accuracy(
    y_true,
    probabilities,
    class_names,
    k=3,
):
    top_k_indices = (
        probabilities
        .argsort(axis=1)[:, -k:]
    )

    correct = 0

    for index, target in enumerate(y_true):
        predicted_classes = {
            class_names[i]
            for i in top_k_indices[index]
        }

        if target in predicted_classes:
            correct += 1

    return correct / len(y_true)


def main():
    MODEL_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    REPORT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    print("=" * 70)
    print("PayMind Payment Method Model V1")
    print("=" * 70)

    print("\nLoading training data...")
    X_train, y_train = load_features(
        TRAIN_PATH
    )

    print("Loading validation data...")
    X_validation, y_validation = load_features(
        VALIDATION_PATH
    )

    print("Loading test data...")
    X_test, y_test = load_features(
        TEST_PATH
    )

    feature_names = get_feature_names(
        "payment_method"
    )

    categorical_features = (
        get_categorical_features(
            "payment_method"
        )
    )

    print()
    print(f"Training rows:    {len(X_train):,}")
    print(
        f"Validation rows:  "
        f"{len(X_validation):,}"
    )
    print(f"Test rows:        {len(X_test):,}")
    print(
        f"Training classes: "
        f"{y_train.nunique()}"
    )

    print("\nFeatures:")
    for feature in feature_names:
        print(f"  {feature}")

    print("\nTraining CatBoost...")

    model = CatBoostClassifier(
        loss_function="MultiClass",
        eval_metric="MultiClass",
        iterations=1000,
        learning_rate=0.05,
        depth=8,
        random_seed=42,
        verbose=100,
        allow_writing_files=False,
    )

    model.fit(
        X_train,
        y_train,
        cat_features=categorical_features,
        eval_set=(
            X_validation,
            y_validation,
        ),
        early_stopping_rounds=100,
        use_best_model=True,
    )

    print("\nEvaluating test set...")

    predictions = model.predict(
        X_test
    ).reshape(-1)

    probabilities = model.predict_proba(
        X_test
    )

    class_names = list(
        model.classes_
    )

    accuracy = accuracy_score(
        y_test,
        predictions,
    )

    loss = log_loss(
        y_test,
        probabilities,
        labels=class_names,
    )

    top3 = top_k_accuracy(
        y_test.tolist(),
        probabilities,
        class_names,
        k=3,
    )

    report_text = classification_report(
        y_test,
        predictions,
        zero_division=0,
    )

    print()
    print("=" * 70)
    print("TEST RESULTS")
    print("=" * 70)

    print(
        f"Top-1 Accuracy: "
        f"{accuracy:.4f}"
    )

    print(
        f"Top-3 Accuracy: "
        f"{top3:.4f}"
    )

    print(
        f"Log Loss:       "
        f"{loss:.4f}"
    )

    print()
    print(report_text)

    model_path = (
        MODEL_DIR /
        "payment_method_v1.cbm"
    )

    model.save_model(
        str(model_path)
    )

    feature_importance = dict(
        zip(
            feature_names,
            model.get_feature_importance(),
        )
    )

    metadata = {
        "name":
            "paymind-payment-method",
        "version":
            "1.0.0",
        "algorithm":
            "CatBoostClassifier",
        "objective":
            "MultiClass",
        "trained_at":
            datetime.now(
                timezone.utc
            ).isoformat(),
        "training_rows":
            len(X_train),
        "validation_rows":
            len(X_validation),
        "test_rows":
            len(X_test),
        "classes":
            class_names,
        "features":
            feature_names,
        "categorical_features":
            categorical_features,
        "metrics": {
            "top1_accuracy":
                accuracy,
            "top3_accuracy":
                top3,
            "log_loss":
                loss,
        },
        "feature_importance":
            feature_importance,
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
        "payment_method_model_v1.txt"
    )

    report_path.write_text(
        (
            f"Top-1 Accuracy: "
            f"{accuracy:.4f}\n"
            f"Top-3 Accuracy: "
            f"{top3:.4f}\n"
            f"Log Loss: "
            f"{loss:.4f}\n\n"
            f"{report_text}"
        ),
        encoding="utf-8",
    )

    print()
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


if __name__ == "__main__":
    main()