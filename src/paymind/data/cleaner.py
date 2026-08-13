from __future__ import annotations

from pathlib import Path
import json

import duckdb


RAW_DIR = Path("data/training")
PROCESSED_DIR = Path("data/processed")
REPORT_DIR = Path("data/reports")


FILES = {
    "payment_method": RAW_DIR / "payment_method.csv",
    "success": RAW_DIR / "success.csv",
    "arrival": RAW_DIR / "arrival.csv",
}


VALID_CURRENCIES = {
    "AUD",
    "USD",
    "GBP",
    "EUR",
    "IDR",
    "HKD",
    "MYR",
    "NZD",
    "SGD",
    "INR",
    "MXN",
    "BRL",
    "THB",
    "COP",
    "CHF",
    "VND",
    "CAD",
    "AED",
    "ZAR",
    "JPY",
    "CNY",
    "PHP",
}


# Do NOT permanently delete rare classes yet.
# For payment-method prediction we map very small classes to OTHER.
MIN_PAYMENT_METHOD_ROWS = 100


# Temporary V1 protection against corrupted/extreme arrival labels.
# 30 days.
MAX_ARRIVAL_MINUTES = 30 * 24 * 60


def sql_path(path: Path) -> str:
    return str(path.resolve()).replace("'", "''")


def currency_sql() -> str:
    return ", ".join(
        f"'{currency}'"
        for currency in sorted(VALID_CURRENCIES)
    )


def payment_method_source() -> str:
    return f"""
    read_csv(
        '{sql_path(FILES["payment_method"])}',
        header=true,
        nullstr='\\N',
        columns={{
            'event_id': 'VARCHAR',
            'timestamp_utc': 'VARCHAR',
            'transaction_type': 'VARCHAR',
            'country': 'VARCHAR',
            'ip_country': 'VARCHAR',
            'jurisdiction': 'VARCHAR',
            'currency': 'VARCHAR',
            'local_currency': 'VARCHAR',
            'amount': 'DOUBLE',
            'app_type': 'VARCHAR',
            'hour': 'INTEGER',
            'day_of_week': 'VARCHAR',
            'is_weekend': 'INTEGER',
            'is_cross_border': 'INTEGER',
            'payment_type': 'VARCHAR'
        }}
    )
    """


def success_source() -> str:
    return f"""
    read_csv(
        '{sql_path(FILES["success"])}',
        header=true,
        nullstr='\\N',
        columns={{
            'timestamp_utc': 'VARCHAR',
            'transaction_type': 'VARCHAR',
            'currency': 'VARCHAR',
            'amount': 'DOUBLE',
            'hour': 'INTEGER',
            'day_of_week': 'VARCHAR',
            'is_weekend': 'INTEGER',
            'is_cross_border': 'INTEGER',
            'payment_code': 'VARCHAR',
            'payment_type': 'VARCHAR',
            'success': 'INTEGER'
        }}
    )
    """


def arrival_source() -> str:
    return f"""
    read_csv(
        '{sql_path(FILES["arrival"])}',
        header=true,
        nullstr='\\N',
        columns={{
            'timestamp_utc': 'VARCHAR',
            'transaction_type': 'VARCHAR',
            'currency': 'VARCHAR',
            'amount': 'DOUBLE',
            'hour': 'INTEGER',
            'day_of_week': 'VARCHAR',
            'is_weekend': 'INTEGER',
            'is_cross_border': 'INTEGER',
            'payment_code': 'VARCHAR',
            'payment_type': 'VARCHAR',
            'banking_hours_indicator': 'INTEGER',
            'arrival_duration_minutes': 'DOUBLE'
        }}
    )
    """


def clean_payment_method(
    con: duckdb.DuckDBPyConnection,
) -> dict:
    source = payment_method_source()

    output = (
        PROCESSED_DIR /
        "payment_method_clean.csv"
    )

    raw_count = con.execute(
        f"SELECT COUNT(*) FROM {source}"
    ).fetchone()[0]

    method_counts = con.execute(
        f"""
        SELECT
            LOWER(TRIM(payment_type)) AS payment_type,
            COUNT(*) AS rows
        FROM {source}
        WHERE payment_type IS NOT NULL
          AND TRIM(payment_type) <> ''
        GROUP BY 1
        """
    ).fetchall()

    valid_methods = {
        row[0]
        for row in method_counts
        if row[1] >= MIN_PAYMENT_METHOD_ROWS
    }

    valid_method_sql = ", ".join(
        f"'{method}'"
        for method in sorted(valid_methods)
    )

    con.execute(
        f"""
        COPY (
            SELECT DISTINCT

                timestamp_utc,

                LOWER(TRIM(transaction_type))
                    AS transaction_type,

                NULLIF(
                    UPPER(TRIM(country)),
                    ''
                ) AS country,

                NULLIF(
                    UPPER(TRIM(ip_country)),
                    ''
                ) AS ip_country,

                NULLIF(
                    UPPER(TRIM(jurisdiction)),
                    ''
                ) AS jurisdiction,

                UPPER(TRIM(currency))
                    AS currency,

                NULLIF(
                    UPPER(TRIM(local_currency)),
                    ''
                ) AS local_currency,

                amount,

                UPPER(TRIM(app_type))
                    AS app_type,

                hour,

                TRIM(day_of_week)
                    AS day_of_week,

                is_weekend,

                is_cross_border,

                CASE
                    WHEN LOWER(TRIM(payment_type))
                         IN ({valid_method_sql})
                    THEN LOWER(TRIM(payment_type))
                    ELSE 'other'
                END AS payment_type

            FROM {source}

            WHERE amount > 0

              AND payment_type IS NOT NULL
              AND TRIM(payment_type) <> ''

              AND currency IS NOT NULL
              AND UPPER(TRIM(currency))
                  IN ({currency_sql()})
        )
        TO '{sql_path(output)}'
        (
            HEADER,
            DELIMITER ','
        )
        """
    )

    clean_count = con.execute(
        f"""
        SELECT COUNT(*)
        FROM read_csv_auto(
            '{sql_path(output)}',
            header=true
        )
        """
    ).fetchone()[0]

    return {
        "raw_rows": raw_count,
        "clean_rows": clean_count,
        "removed_rows": raw_count - clean_count,
        "minimum_payment_method_rows":
            MIN_PAYMENT_METHOD_ROWS,
        "retained_payment_methods":
            sorted(valid_methods),
    }


def clean_success(
    con: duckdb.DuckDBPyConnection,
) -> dict:
    source = success_source()

    output = (
        PROCESSED_DIR /
        "success_clean.csv"
    )

    raw_count = con.execute(
        f"SELECT COUNT(*) FROM {source}"
    ).fetchone()[0]

    con.execute(
        f"""
        COPY (
            SELECT DISTINCT

                timestamp_utc,

                LOWER(TRIM(transaction_type))
                    AS transaction_type,

                UPPER(TRIM(currency))
                    AS currency,

                amount,

                hour,

                TRIM(day_of_week)
                    AS day_of_week,

                is_weekend,

                is_cross_border,

                LOWER(TRIM(payment_code))
                    AS payment_code,

                LOWER(TRIM(payment_type))
                    AS payment_type,

                success

            FROM {source}

            WHERE amount > 0

              AND currency IS NOT NULL
              AND UPPER(TRIM(currency))
                  IN ({currency_sql()})

              AND payment_code IS NOT NULL
              AND TRIM(payment_code) <> ''

              AND payment_type IS NOT NULL
              AND TRIM(payment_type) <> ''

              AND success IN (0, 1)
        )
        TO '{sql_path(output)}'
        (
            HEADER,
            DELIMITER ','
        )
        """
    )

    clean_count = con.execute(
        f"""
        SELECT COUNT(*)
        FROM read_csv_auto(
            '{sql_path(output)}',
            header=true
        )
        """
    ).fetchone()[0]

    return {
        "raw_rows": raw_count,
        "clean_rows": clean_count,
        "removed_rows": raw_count - clean_count,
    }


def clean_arrival(
    con: duckdb.DuckDBPyConnection,
) -> dict:
    source = arrival_source()

    output = (
        PROCESSED_DIR /
        "arrival_clean.csv"
    )

    raw_count = con.execute(
        f"SELECT COUNT(*) FROM {source}"
    ).fetchone()[0]

    con.execute(
        f"""
        COPY (
            SELECT DISTINCT

                timestamp_utc,

                LOWER(TRIM(transaction_type))
                    AS transaction_type,

                UPPER(TRIM(currency))
                    AS currency,

                amount,

                hour,

                TRIM(day_of_week)
                    AS day_of_week,

                is_weekend,

                is_cross_border,

                LOWER(TRIM(payment_code))
                    AS payment_code,

                LOWER(TRIM(payment_type))
                    AS payment_type,

                banking_hours_indicator,

                arrival_duration_minutes

            FROM {source}

            WHERE amount > 0

              AND currency IS NOT NULL
              AND UPPER(TRIM(currency))
                  IN ({currency_sql()})

              AND payment_code IS NOT NULL
              AND TRIM(payment_code) <> ''

              AND payment_type IS NOT NULL
              AND TRIM(payment_type) <> ''

              AND arrival_duration_minutes
                  IS NOT NULL

              AND arrival_duration_minutes >= 0

              AND arrival_duration_minutes
                  <= {MAX_ARRIVAL_MINUTES}
        )
        TO '{sql_path(output)}'
        (
            HEADER,
            DELIMITER ','
        )
        """
    )

    clean_count = con.execute(
        f"""
        SELECT COUNT(*)
        FROM read_csv_auto(
            '{sql_path(output)}',
            header=true
        )
        """
    ).fetchone()[0]

    return {
        "raw_rows": raw_count,
        "clean_rows": clean_count,
        "removed_rows": raw_count - clean_count,
        "maximum_arrival_minutes":
            MAX_ARRIVAL_MINUTES,
    }


def main() -> None:
    PROCESSED_DIR.mkdir(
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
        print("PayMind Data Cleaner")
        print("=" * 70)

        if FILES["payment_method"].exists():
            print("\nCleaning payment method data...")
            report["payment_method"] = (
                clean_payment_method(con)
            )

        if FILES["success"].exists():
            print("\nCleaning success data...")
            report["success"] = (
                clean_success(con)
            )

        if FILES["arrival"].exists():
            print("\nCleaning arrival data...")
            report["arrival"] = (
                clean_arrival(con)
            )

    finally:
        con.close()

    report_file = (
        REPORT_DIR /
        "cleaning_report.json"
    )

    report_file.write_text(
        json.dumps(
            report,
            indent=2,
        ),
        encoding="utf-8",
    )

    print()
    print("=" * 70)

    for dataset, stats in report.items():
        print(
            f"{dataset:20}"
            f"raw={stats['raw_rows']:,} "
            f"clean={stats['clean_rows']:,} "
            f"removed={stats['removed_rows']:,}"
        )

    print()
    print(
        f"Cleaning report: {report_file}"
    )

    print("=" * 70)


if __name__ == "__main__":
    main()