# Data Schemas

These are the exact required headers for the local training CSV workflow.

## `payment_method.csv`

```text
event_id,timestamp_utc,transaction_type,country,ip_country,jurisdiction,currency,local_currency,amount,app_type,hour,day_of_week,is_weekend,is_cross_border,payment_type
```

## `success.csv`

```text
timestamp_utc,transaction_type,currency,amount,hour,day_of_week,is_weekend,is_cross_border,payment_code,payment_type,success
```

## `arrival.csv`

```text
timestamp_utc,transaction_type,currency,amount,hour,day_of_week,is_weekend,is_cross_border,payment_code,payment_type,banking_hours_indicator,arrival_duration_minutes
```

## Notes

- `timestamp_utc` should be chronological and consistently formatted.
- `success` must be binary `0` or `1`.
- `arrival_duration_minutes` must use one consistent business definition across the full dataset.
- The synthetic files in `examples/csv/` are schema examples only and are not intended to produce useful model quality.
