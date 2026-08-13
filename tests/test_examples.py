import csv
from pathlib import Path

from paymind.training.schemas import ARRIVAL_COLUMNS, PAYMENT_METHOD_COLUMNS, SUCCESS_COLUMNS


def header(path: str) -> list[str]:
    with Path(path).open(newline="", encoding="utf-8") as handle:
        return next(csv.reader(handle))


def test_example_payment_method_csv_schema():
    assert header("examples/csv/payment_method_template.csv") == PAYMENT_METHOD_COLUMNS


def test_example_success_csv_schema():
    assert header("examples/csv/success_template.csv") == SUCCESS_COLUMNS


def test_example_arrival_csv_schema():
    assert header("examples/csv/arrival_template.csv") == ARRIVAL_COLUMNS
