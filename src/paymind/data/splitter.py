from __future__ import annotations

from pathlib import Path
import json

import duckdb


PROCESSED_DIR = Path("data/processed")
SPLIT_DIR = Path("data/splits")
REPORT_DIR = Path("data/reports")


DATASETS = {
    "payment_method": (
        PROCESSED_DIR / "payment_method_clean.csv"
    ),
    "success": (
        PROCESSED_DIR / "success_clean.csv"
    ),
    "arrival": (
        PROCESSED_DIR / "arrival_clean.csv"
    ),
}


# V1 chronological split.
#
# Train:
# everything before 2025
#
# Validation:
# calendar year 2025
#
# Test:
# 2026 onwards
#
TRAIN_END = "2025-01-01 00:00:00"
VALIDATION_END = "2026-01-01 00:00:00"


def sql_path(path: Path) -> str:
    return str(
        path.resolve()
    ).replace(
        "'",
        "''",
    )


def timestamp_expr() -> str:
    return """
    COALESCE(
    TRY_CAST(timestamp_utc AS TIMESTAMP),

    TRY_STRPTIME(
        CAST(timestamp_utc AS VARCHAR),
        '%m/%d/%y %H:%M'
    ),

    TRY_STRPTIME(
        CAST(timestamp_utc AS VARCHAR),
        '%m/%d/%Y %H:%M'
    )
)
    """


def reader(path: Path) -> str:
    return f"""
    read_csv_auto(
        '{sql_path(path)}',
        header=true,
        all_varchar=false
    )
    """


def create_split(
    con: duckdb.DuckDBPyConnection,
    dataset_name: str,
    source_path: Path,
) -> dict:
    source = reader(source_path)
    ts = timestamp_expr()

    dataset_dir = (
        SPLIT_DIR /
        dataset_name
    )

    dataset_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    train_path = (
        dataset_dir /
        "train.csv"
    )

    validation_path = (
        dataset_dir /
        "validation.csv"
    )

    test_path = (
        dataset_dir /
        "test.csv"
    )

    # TRAIN
    con.execute(
        f"""
        COPY (
            SELECT *
            FROM {source}

            WHERE {ts}
                < TIMESTAMP '{TRAIN_END}'

            ORDER BY {ts}
        )

        TO '{sql_path(train_path)}'
        (
            HEADER,
            DELIMITER ','
        )
        """
    )

    # VALIDATION
    con.execute(
        f"""
        COPY (
            SELECT *
            FROM {source}

            WHERE {ts}
                >= TIMESTAMP '{TRAIN_END}'

              AND {ts}
                < TIMESTAMP '{VALIDATION_END}'

            ORDER BY {ts}
        )

        TO '{sql_path(validation_path)}'
        (
            HEADER,
            DELIMITER ','
        )
        """
    )

    # TEST
    con.execute(
        f"""
        COPY (
            SELECT *
            FROM {source}

            WHERE {ts}
                >= TIMESTAMP '{VALIDATION_END}'

            ORDER BY {ts}
        )

        TO '{sql_path(test_path)}'
        (
            HEADER,
            DELIMITER ','
        )
        """
    )

    train_count = con.execute(
        f"""
        SELECT COUNT(*)
        FROM read_csv_auto(
            '{sql_path(train_path)}',
            header=true
        )
        """
    ).fetchone()[0]

    validation_count = con.execute(
        f"""
        SELECT COUNT(*)
        FROM read_csv_auto(
            '{sql_path(validation_path)}',
            header=true
        )
        """
    ).fetchone()[0]

    test_count = con.execute(
        f"""
        SELECT COUNT(*)
        FROM read_csv_auto(
            '{sql_path(test_path)}',
            header=true
        )
        """
    ).fetchone()[0]

    total = (
        train_count
        + validation_count
        + test_count
    )

    source_count = con.execute(
        f"""
        SELECT COUNT(*)
        FROM {source}
        """
    ).fetchone()[0]

    print()
    print(dataset_name.upper())
    print("-" * 60)

    print(
        f"Source:      "
        f"{source_count:,}"
    )

    print(
        f"Train:       "
        f"{train_count:,}"
    )

    print(
        f"Validation:  "
        f"{validation_count:,}"
    )

    print(
        f"Test:        "
        f"{test_count:,}"
    )

    if total != source_count:
        print(
            "WARNING: split counts "
            "do not equal source count."
        )

    return {
        "source_rows": source_count,
        "train_rows": train_count,
        "validation_rows": validation_count,
        "test_rows": test_count,
        "train_end": TRAIN_END,
        "validation_end":
            VALIDATION_END,
    }


def check_payment_method_classes(
    con: duckdb.DuckDBPyConnection,
) -> dict:
    """
    Check whether payment classes in the
    test period were ever seen during training.
    """

    train_path = (
        SPLIT_DIR /
        "payment_method" /
        "train.csv"
    )

    validation_path = (
        SPLIT_DIR /
        "payment_method" /
        "validation.csv"
    )

    test_path = (
        SPLIT_DIR /
        "payment_method" /
        "test.csv"
    )

    train_classes = {
        row[0]
        for row in con.execute(
            f"""
            SELECT DISTINCT payment_type
            FROM read_csv_auto(
                '{sql_path(train_path)}',
                header=true
            )
            """
        ).fetchall()
    }

    validation_classes = {
        row[0]
        for row in con.execute(
            f"""
            SELECT DISTINCT payment_type
            FROM read_csv_auto(
                '{sql_path(validation_path)}',
                header=true
            )
            """
        ).fetchall()
    }

    test_classes = {
        row[0]
        for row in con.execute(
            f"""
            SELECT DISTINCT payment_type
            FROM read_csv_auto(
                '{sql_path(test_path)}',
                header=true
            )
            """
        ).fetchall()
    }

    unseen_validation = sorted(
        validation_classes
        - train_classes
    )

    unseen_test = sorted(
        test_classes
        - train_classes
    )

    print()
    print("PAYMENT METHOD CLASS CHECK")
    print("-" * 60)

    print(
        "Training classes:",
        len(train_classes),
    )

    print(
        "Validation unseen classes:",
        unseen_validation,
    )

    print(
        "Test unseen classes:",
        unseen_test,
    )

    return {
        "training_classes":
            sorted(train_classes),
        "unseen_validation_classes":
            unseen_validation,
        "unseen_test_classes":
            unseen_test,
    }


def main() -> None:
    SPLIT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    REPORT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    con = duckdb.connect()

    report = {}

    try:
        print("=" * 70)
        print("PayMind Dataset Splitter")
        print("=" * 70)

        for (
            dataset_name,
            source_path,
        ) in DATASETS.items():

            if not source_path.exists():
                print(
                    "Missing processed dataset:",
                    source_path,
                )
                continue

            report[dataset_name] = (
                create_split(
                    con,
                    dataset_name,
                    source_path,
                )
            )

        payment_method_path = (
            DATASETS[
                "payment_method"
            ]
        )

        if payment_method_path.exists():
            report[
                "payment_method_class_check"
            ] = check_payment_method_classes(
                con
            )

    finally:
        con.close()

    report_path = (
        REPORT_DIR /
        "split_report.json"
    )

    report_path.write_text(
        json.dumps(
            report,
            indent=2,
        ),
        encoding="utf-8",
    )

    print()
    print("=" * 70)
    print(
        "Split report:",
        report_path,
    )
    print("=" * 70)


if __name__ == "__main__":
    main()