from pathlib import Path
import json

import duckdb


DATA_DIR = Path("data/training")
REPORT_DIR = Path("data/reports")


FILES = {
    "payment_method": DATA_DIR / "payment_method.csv",
    "success": DATA_DIR / "success.csv",
    "arrival": DATA_DIR / "arrival.csv",
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


def path_sql(path: Path) -> str:
    return str(path.resolve()).replace("'", "''")


def payment_method_reader(path: Path) -> str:
    return f"""
    read_csv(
        '{path_sql(path)}',
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


def success_reader(path: Path) -> str:
    return f"""
    read_csv(
        '{path_sql(path)}',
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


def arrival_reader(path: Path) -> str:
    return f"""
    read_csv(
        '{path_sql(path)}',
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


def timestamp_sql() -> str:
    return """
    COALESCE(
        TRY_STRPTIME(timestamp_utc, '%m/%d/%y %H:%M'),
        TRY_STRPTIME(timestamp_utc, '%m/%d/%Y %H:%M'),
        TRY_STRPTIME(timestamp_utc, '%Y-%m-%d %H:%M:%S')
    )
    """


def print_rows(title, rows):
    print()
    print(title)
    print("-" * 70)

    for row in rows:
        print("  ", *row)


def inspect_payment_method(con, path):
    reader = payment_method_reader(path)
    ts = timestamp_sql()

    stats = con.execute(
        f"""
        SELECT
            COUNT(*) AS rows,

            MIN({ts}) AS first_record,
            MAX({ts}) AS last_record,

            COUNT(*) FILTER (
                WHERE {ts} IS NULL
            ) AS invalid_timestamps,

            COUNT(*) FILTER (
                WHERE amount IS NULL OR amount <= 0
            ) AS invalid_amounts,

            COUNT(*) FILTER (
                WHERE currency IS NULL
            ) AS missing_currency,

            COUNT(*) FILTER (
                WHERE payment_type IS NULL
                   OR TRIM(payment_type) = ''
            ) AS missing_payment_type,

            COUNT(DISTINCT payment_type)
                AS payment_type_count

        FROM {reader}
        """
    ).fetchone()

    methods = con.execute(
        f"""
        SELECT
            payment_type,
            COUNT(*) AS transactions,

            ROUND(
                100.0 * COUNT(*) /
                SUM(COUNT(*)) OVER (),
                2
            ) AS percentage

        FROM {reader}

        GROUP BY payment_type
        ORDER BY transactions DESC
        """
    ).fetchall()

    currencies = con.execute(
        f"""
        SELECT
            currency,
            COUNT(*) AS transactions

        FROM {reader}

        GROUP BY currency
        ORDER BY transactions DESC
        """
    ).fetchall()

    valid_currency_sql = ",".join(
        f"'{currency}'"
        for currency in sorted(VALID_CURRENCIES)
    )

    suspicious = con.execute(
        f"""
        SELECT
            currency,
            COUNT(*) AS rows

        FROM {reader}

        WHERE currency IS NOT NULL
          AND UPPER(TRIM(currency))
              NOT IN ({valid_currency_sql})

        GROUP BY currency
        ORDER BY rows DESC
        """
    ).fetchall()

    by_year = con.execute(
        f"""
        SELECT
            EXTRACT(YEAR FROM {ts}) AS year,
            payment_type,
            COUNT(*) AS transactions

        FROM {reader}

        WHERE {ts} IS NOT NULL

        GROUP BY year, payment_type
        ORDER BY year, transactions DESC
        """
    ).fetchall()

    print()
    print("=" * 70)
    print("PAYMENT METHOD DATASET")
    print("=" * 70)

    print(f"Rows:                 {stats[0]:,}")
    print(f"Date range:           {stats[1]} -> {stats[2]}")
    print(f"Invalid timestamps:   {stats[3]:,}")
    print(f"Invalid amounts:      {stats[4]:,}")
    print(f"Missing currency:     {stats[5]:,}")
    print(f"Missing target:       {stats[6]:,}")
    print(f"Payment types:        {stats[7]:,}")

    print_rows(
        "Payment Method Distribution",
        methods
    )

    print_rows(
        "Currency Distribution",
        currencies
    )

    print_rows(
        "Suspicious Currency Values",
        suspicious
    )

    return {
        "rows": stats[0],
        "first_record": str(stats[1]),
        "last_record": str(stats[2]),
        "invalid_timestamps": stats[3],
        "invalid_amounts": stats[4],
        "missing_currency": stats[5],
        "missing_target": stats[6],
        "payment_type_count": stats[7],
        "payment_methods": methods,
        "currencies": currencies,
        "suspicious_currencies": suspicious,
        "by_year": by_year,
    }


def inspect_success(con, path):
    reader = success_reader(path)
    ts = timestamp_sql()

    stats = con.execute(
        f"""
        SELECT
            COUNT(*) AS rows,

            COUNT(*) FILTER (
                WHERE success = 1
            ) AS successes,

            COUNT(*) FILTER (
                WHERE success = 0
            ) AS failures,

            COUNT(*) FILTER (
                WHERE success IS NULL
                   OR success NOT IN (0,1)
            ) AS invalid_targets,

            ROUND(
                AVG(success)
                FILTER (
                    WHERE success IN (0,1)
                ) * 100,
                2
            ) AS success_rate,

            MIN({ts}) AS first_record,
            MAX({ts}) AS last_record,

            COUNT(*) FILTER (
                WHERE {ts} IS NULL
            ) AS invalid_timestamps

        FROM {reader}
        """
    ).fetchone()

    by_method = con.execute(
        f"""
        SELECT
            payment_type,
            COUNT(*) AS attempts,

            COUNT(*) FILTER (
                WHERE success = 1
            ) AS successes,

            COUNT(*) FILTER (
                WHERE success = 0
            ) AS failures,

            ROUND(
                AVG(success) * 100,
                2
            ) AS success_rate

        FROM {reader}

        WHERE success IN (0,1)

        GROUP BY payment_type
        ORDER BY attempts DESC
        """
    ).fetchall()

    by_year = con.execute(
        f"""
        SELECT
            EXTRACT(YEAR FROM {ts}) AS year,

            COUNT(*) AS attempts,

            COUNT(*) FILTER (
                WHERE success = 1
            ) AS successes,

            COUNT(*) FILTER (
                WHERE success = 0
            ) AS failures,

            ROUND(
                AVG(success) * 100,
                2
            ) AS success_rate

        FROM {reader}

        WHERE success IN (0,1)
          AND {ts} IS NOT NULL

        GROUP BY year
        ORDER BY year
        """
    ).fetchall()

    print()
    print("=" * 70)
    print("SUCCESS DATASET")
    print("=" * 70)

    print(f"Rows:                 {stats[0]:,}")
    print(f"Successes:            {stats[1]:,}")
    print(f"Failures:             {stats[2]:,}")
    print(f"Invalid targets:      {stats[3]:,}")
    print(f"Success rate:         {stats[4]}%")
    print(f"Date range:           {stats[5]} -> {stats[6]}")
    print(f"Invalid timestamps:   {stats[7]:,}")

    print_rows(
        "Success by Payment Method",
        by_method
    )

    print_rows(
        "Success by Year",
        by_year
    )

    return {
        "rows": stats[0],
        "successes": stats[1],
        "failures": stats[2],
        "invalid_targets": stats[3],
        "success_rate": stats[4],
        "first_record": str(stats[5]),
        "last_record": str(stats[6]),
        "invalid_timestamps": stats[7],
        "by_method": by_method,
        "by_year": by_year,
    }


def inspect_arrival(con, path):
    reader = arrival_reader(path)
    ts = timestamp_sql()

    stats = con.execute(
        f"""
        SELECT
            COUNT(*) AS rows,

            COUNT(*) FILTER (
                WHERE arrival_duration_minutes IS NULL
            ) AS missing_target,

            COUNT(*) FILTER (
                WHERE arrival_duration_minutes < 0
            ) AS negative_duration,

            COUNT(*) FILTER (
                WHERE arrival_duration_minutes = 0
            ) AS zero_duration,

            ROUND(
                AVG(arrival_duration_minutes)
                FILTER (
                    WHERE arrival_duration_minutes >= 0
                ),
                2
            ) AS mean_minutes,

            ROUND(
                MEDIAN(arrival_duration_minutes)
                FILTER (
                    WHERE arrival_duration_minutes >= 0
                ),
                2
            ) AS p50_minutes,

            ROUND(
                QUANTILE_CONT(
                    arrival_duration_minutes,
                    0.90
                )
                FILTER (
                    WHERE arrival_duration_minutes >= 0
                ),
                2
            ) AS p90_minutes,

            ROUND(
                QUANTILE_CONT(
                    arrival_duration_minutes,
                    0.95
                )
                FILTER (
                    WHERE arrival_duration_minutes >= 0
                ),
                2
            ) AS p95_minutes,

            ROUND(
                QUANTILE_CONT(
                    arrival_duration_minutes,
                    0.99
                )
                FILTER (
                    WHERE arrival_duration_minutes >= 0
                ),
                2
            ) AS p99_minutes,

            MAX(arrival_duration_minutes)
                AS maximum_minutes,

            MIN({ts}) AS first_record,
            MAX({ts}) AS last_record

        FROM {reader}
        """
    ).fetchone()

    by_method = con.execute(
        f"""
        SELECT
            payment_type,

            COUNT(*) AS payments,

            COUNT(*) FILTER (
                WHERE arrival_duration_minutes = 0
            ) AS zero_duration,

            ROUND(
                MEDIAN(arrival_duration_minutes),
                2
            ) AS p50,

            ROUND(
                QUANTILE_CONT(
                    arrival_duration_minutes,
                    0.90
                ),
                2
            ) AS p90,

            ROUND(
                AVG(arrival_duration_minutes),
                2
            ) AS mean

        FROM {reader}

        WHERE arrival_duration_minutes >= 0

        GROUP BY payment_type
        ORDER BY payments DESC
        """
    ).fetchall()

    by_year = con.execute(
        f"""
        SELECT
            EXTRACT(YEAR FROM {ts}) AS year,

            COUNT(*) AS payments,

            ROUND(
                MEDIAN(arrival_duration_minutes),
                2
            ) AS p50,

            ROUND(
                QUANTILE_CONT(
                    arrival_duration_minutes,
                    0.90
                ),
                2
            ) AS p90

        FROM {reader}

        WHERE {ts} IS NOT NULL
          AND arrival_duration_minutes >= 0

        GROUP BY year
        ORDER BY year
        """
    ).fetchall()

    print()
    print("=" * 70)
    print("ARRIVAL DATASET")
    print("=" * 70)

    print(f"Rows:                 {stats[0]:,}")
    print(f"Missing target:       {stats[1]:,}")
    print(f"Negative duration:    {stats[2]:,}")
    print(f"Zero-minute arrival:  {stats[3]:,}")
    print(f"Mean:                 {stats[4]} min")
    print(f"P50:                  {stats[5]} min")
    print(f"P90:                  {stats[6]} min")
    print(f"P95:                  {stats[7]} min")
    print(f"P99:                  {stats[8]} min")
    print(f"Maximum:              {stats[9]} min")
    print(f"Date range:           {stats[10]} -> {stats[11]}")

    print_rows(
        "Arrival by Payment Method",
        by_method
    )

    print_rows(
        "Arrival by Year",
        by_year
    )

    return {
        "rows": stats[0],
        "missing_target": stats[1],
        "negative_duration": stats[2],
        "zero_duration": stats[3],
        "mean_minutes": stats[4],
        "p50_minutes": stats[5],
        "p90_minutes": stats[6],
        "p95_minutes": stats[7],
        "p99_minutes": stats[8],
        "maximum_minutes": stats[9],
        "first_record": str(stats[10]),
        "last_record": str(stats[11]),
        "by_method": by_method,
        "by_year": by_year,
    }


def main():
    REPORT_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    con = duckdb.connect()

    report = {}

    try:
        if FILES["payment_method"].exists():
            report["payment_method"] = (
                inspect_payment_method(
                    con,
                    FILES["payment_method"]
                )
            )

        if FILES["success"].exists():
            report["success"] = (
                inspect_success(
                    con,
                    FILES["success"]
                )
            )

        if FILES["arrival"].exists():
            report["arrival"] = (
                inspect_arrival(
                    con,
                    FILES["arrival"]
                )
            )

    finally:
        con.close()

    output = (
        REPORT_DIR /
        "training_data_report.json"
    )

    output.write_text(
        json.dumps(
            report,
            indent=2,
            default=str
        ),
        encoding="utf-8"
    )

    print()
    print("=" * 70)
    print(
        f"Report saved to: {output}"
    )
    print("=" * 70)


if __name__ == "__main__":
    main()