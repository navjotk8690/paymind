from pathlib import Path

import duckdb


PATH = Path(
    "data/processed/arrival_clean.csv"
).resolve()


def main():
    con = duckdb.connect()

    source = f"""
        read_csv_auto(
            '{str(PATH)}',
            header=true
        )
    """

    print("=" * 70)
    print("ARRIVAL TARGET DIAGNOSTICS")
    print("=" * 70)

    # Most common exact arrival times
    rows = con.execute(
        f"""
        SELECT
            ROUND(
                arrival_duration_minutes,
                2
            ) AS minutes,

            COUNT(*) AS rows,

            ROUND(
                100.0 * COUNT(*) /
                SUM(COUNT(*)) OVER (),
                2
            ) AS percentage

        FROM {source}

        GROUP BY 1
        ORDER BY rows DESC

        LIMIT 30
        """
    ).fetchall()

    print("\nMost common exact durations")
    print("-" * 70)

    for minutes, count, percentage in rows:
        print(
            f"{minutes:12.2f} min "
            f"{count:10,} "
            f"{percentage:7.2f}%"
        )

    # Rounded to nearest hour
    rows = con.execute(
        f"""
        SELECT
            ROUND(
                arrival_duration_minutes / 60
            ) AS hours,

            COUNT(*) AS rows,

            ROUND(
                100.0 * COUNT(*) /
                SUM(COUNT(*)) OVER (),
                2
            ) AS percentage

        FROM {source}

        GROUP BY 1
        ORDER BY rows DESC

        LIMIT 30
        """
    ).fetchall()

    print("\nArrival rounded to nearest hour")
    print("-" * 70)

    for hours, count, percentage in rows:
        print(
            f"{hours:8.0f} hours "
            f"{count:10,} "
            f"{percentage:7.2f}%"
        )

    # Distribution buckets
    rows = con.execute(
        f"""
        SELECT
            CASE
                WHEN arrival_duration_minutes = 0
                    THEN '0 min'

                WHEN arrival_duration_minutes <= 5
                    THEN '1-5 min'

                WHEN arrival_duration_minutes <= 30
                    THEN '6-30 min'

                WHEN arrival_duration_minutes <= 60
                    THEN '31-60 min'

                WHEN arrival_duration_minutes <= 180
                    THEN '1-3 hours'

                WHEN arrival_duration_minutes <= 360
                    THEN '3-6 hours'

                WHEN arrival_duration_minutes <= 720
                    THEN '6-12 hours'

                WHEN arrival_duration_minutes <= 1440
                    THEN '12-24 hours'

                WHEN arrival_duration_minutes <= 4320
                    THEN '1-3 days'

                WHEN arrival_duration_minutes <= 10080
                    THEN '3-7 days'

                ELSE '7+ days'
            END AS bucket,

            COUNT(*) AS rows,

            ROUND(
                100.0 * COUNT(*) /
                SUM(COUNT(*)) OVER (),
                2
            ) AS percentage

        FROM {source}

        GROUP BY bucket

        ORDER BY
            MIN(arrival_duration_minutes)
        """
    ).fetchall()

    print("\nArrival distribution")
    print("-" * 70)

    for bucket, count, percentage in rows:
        print(
            f"{bucket:15} "
            f"{count:10,} "
            f"{percentage:7.2f}%"
        )

    # By payment method
    rows = con.execute(
        f"""
        SELECT
            payment_type,

            COUNT(*) AS rows,

            ROUND(
                MEDIAN(
                    arrival_duration_minutes
                ),
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
                MIN(
                    arrival_duration_minutes
                ),
                2
            ) AS minimum,

            ROUND(
                MAX(
                    arrival_duration_minutes
                ),
                2
            ) AS maximum

        FROM {source}

        GROUP BY payment_type
        ORDER BY rows DESC
        """
    ).fetchall()

    print("\nArrival by payment method")
    print("-" * 90)

    for (
        method,
        count,
        p50,
        p90,
        minimum,
        maximum,
    ) in rows:

        print(
            f"{method:22} "
            f"{count:8,} "
            f"P50={p50:10.2f} "
            f"P90={p90:10.2f} "
            f"min={minimum:10.2f} "
            f"max={maximum:10.2f}"
        )

    con.close()


if __name__ == "__main__":
    main()