from __future__ import annotations

import subprocess
import sys
import time
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]


STEPS = [
    (
        "Inspect raw training data",
        [
            sys.executable,
            "scripts/inspect_training_data.py",
        ],
    ),
    (
        "Clean datasets",
        [
            sys.executable,
            "-m",
            "paymind.data.cleaner",
        ],
    ),
    (
        "Create chronological splits",
        [
            sys.executable,
            "-m",
            "paymind.data.splitter",
        ],
    ),
    (
        "Apply payment method class policy",
        [
            sys.executable,
            "-m",
            "paymind.data.payment_method_classes",
        ],
    ),
    (
        "Run feature tests",
        [
            sys.executable,
            "-m",
            "pytest",
            "tests/test_feature_builder.py",
            "-q",
        ],
    ),
    (
        "Train payment method model",
        [
            sys.executable,
            "-m",
            "paymind.training.train_payment_method",
        ],
    ),
    (
        "Train success model",
        [
            sys.executable,
            "-m",
            "paymind.training.train_success",
        ],
    ),
    (
        "Inspect arrival target",
        [
            sys.executable,
            "scripts/inspect_arrival_target.py",
        ],
    ),
    (
        "Train settlement models",
        [
            sys.executable,
            "-m",
            "paymind.training.train_arrival",
        ],
    ),
    (
        "Run model registry tests",
        [
            sys.executable,
            "-m",
            "pytest",
            "tests/test_model_registry.py",
            "-q",
        ],
    ),
    (
        "Run runtime tests",
        [
            sys.executable,
            "-m",
            "pytest",
            "-q",
        ],
    ),
]


def run_step(
    number: int,
    total: int,
    name: str,
    command: list[str],
) -> None:

    print()
    print("=" * 80)
    print(
        f"[{number}/{total}] {name}"
    )
    print("=" * 80)

    print(
        "$",
        " ".join(command),
    )

    started = time.time()

    result = subprocess.run(
        command,
        cwd=PROJECT_ROOT,
    )

    elapsed = time.time() - started

    if result.returncode != 0:
        print()
        print("!" * 80)
        print(
            f"FAILED: {name}"
        )
        print(
            f"Exit code: {result.returncode}"
        )
        print(
            f"Elapsed: {elapsed:.1f}s"
        )
        print("!" * 80)

        sys.exit(
            result.returncode
        )

    print()
    print(
        f"✓ Completed in {elapsed:.1f}s"
    )


def verify_input_files() -> None:

    required = [
        PROJECT_ROOT
        / "data/training/payment_method.csv",

        PROJECT_ROOT
        / "data/training/success.csv",

        PROJECT_ROOT
        / "data/training/arrival.csv",
    ]

    missing = [
        path
        for path in required
        if not path.exists()
    ]

    if missing:
        print(
            "Missing training datasets:"
        )

        for path in missing:
            print(
                f"  - {path}"
            )

        sys.exit(1)


def main() -> None:

    print()
    print("=" * 80)
    print("PayMind Full Training Pipeline")
    print("=" * 80)

    print(
        f"Python: {sys.executable}"
    )

    print(
        f"Project: {PROJECT_ROOT}"
    )

    verify_input_files()

    pipeline_started = time.time()

    total = len(STEPS)

    for number, (
        name,
        command,
    ) in enumerate(
        STEPS,
        start=1,
    ):

        run_step(
            number,
            total,
            name,
            command,
        )

    elapsed = (
        time.time()
        - pipeline_started
    )

    print()
    print("=" * 80)
    print("PAYMIND TRAINING COMPLETE")
    print("=" * 80)

    print(
        f"Total time: {elapsed / 60:.2f} minutes"
    )

    print()
    print("Models:")

    print(
        "  models/payment_method/"
        "payment_method_v1.cbm"
    )

    print(
        "  models/success/"
        "success_v1.cbm"
    )

    print(
        "  models/arrival/"
        "arrival_p50_v1.cbm"
    )

    print(
        "  models/arrival/"
        "arrival_p90_v1.cbm"
    )

    print()
    print("Reports:")

    print(
        "  data/reports/"
    )

    print()
    print(
        "Next: restart the PayMind API "
        "to load the newly trained models."
    )

    print("=" * 80)


if __name__ == "__main__":
    main()