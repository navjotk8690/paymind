from __future__ import annotations

from pathlib import Path
import json

import duckdb


SPLIT_DIR = Path("data/splits/payment_method")
REPORT_DIR = Path("data/reports")

TRAIN_PATH = SPLIT_DIR / "train.csv"
VALIDATION_PATH = SPLIT_DIR / "validation.csv"
TEST_PATH = SPLIT_DIR / "test.csv"


def sql_path(path: Path) -> str:
    return str(path.resolve()).replace("'", "''")


def main() -> None:
    con = duckdb.connect()

    try:
        training_classes = {
            row[0]
            for row in con.execute(
                f"""
                SELECT DISTINCT payment_type
                FROM read_csv_auto(
                    '{sql_path(TRAIN_PATH)}',
                    header=true
                )
                """
            ).fetchall()
        }

        class_sql = ", ".join(
            f"'{value}'"
            for value in sorted(training_classes)
        )

        output_files = {}

        for split_name, input_path in {
            "validation": VALIDATION_PATH,
            "test": TEST_PATH,
        }.items():

            output_path = (
                SPLIT_DIR /
                f"{split_name}_model.csv"
            )

            con.execute(
                f"""
                COPY (
                    SELECT
                        * EXCLUDE (payment_type),

                        CASE
                            WHEN payment_type IN ({class_sql})
                            THEN payment_type
                            ELSE 'other'
                        END AS payment_type

                    FROM read_csv_auto(
                        '{sql_path(input_path)}',
                        header=true
                    )
                )

                TO '{sql_path(output_path)}'
                (
                    HEADER,
                    DELIMITER ','
                )
                """
            )

            output_files[split_name] = str(
                output_path
            )

        report = {
            "training_classes":
                sorted(training_classes),

            "unknown_class_policy":
                "map_to_other",

            "validation_model_file":
                output_files["validation"],

            "test_model_file":
                output_files["test"],
        }

        report_path = (
            REPORT_DIR /
            "payment_method_class_policy.json"
        )

        report_path.write_text(
            json.dumps(
                report,
                indent=2,
            ),
            encoding="utf-8",
        )

        print("=" * 70)
        print("Payment Method Class Policy")
        print("=" * 70)

        print(
            f"Training classes: "
            f"{len(training_classes)}"
        )

        print(
            "Unknown validation/test "
            "classes -> other"
        )

        print()
        print(
            "Created:",
            SPLIT_DIR / "validation_model.csv",
        )

        print(
            "Created:",
            SPLIT_DIR / "test_model.csv",
        )

    finally:
        con.close()


if __name__ == "__main__":
    main()