# Training

Train PayMind locally with your own data. Public arbitrary CSV training is intentionally disabled in the Hugging Face Space.

## Local setup

```bash
git clone <your-fork-of-navcore-paymind>
cd navcore_paymind
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install --upgrade pip
python3 -m pip install -e '.[training]'
```

## Input location

Place your own CSVs under:

- `data/training/payment_method.csv`
- `data/training/success.csv`
- `data/training/arrival.csv`

See `docs/data-schemas.md` for the exact required headers.

## One-command workflow

```bash
python3 scripts/train_all.py
```

The pipeline runs:

1. raw training data inspection
2. cleaning
3. chronological split creation
4. payment-method class policy
5. feature validation
6. payment-method training
7. success training
8. arrival target inspection
9. settlement P50/P90 training
10. tests

Any failing step stops the pipeline immediately.

## Outputs

Generated local artifacts include:

- `models/payment_method/payment_method_v1.cbm`
- `models/success/success_v1.cbm`
- `models/arrival/arrival_p50_v1.cbm`
- `models/arrival/arrival_p90_v1.cbm`

Generated processed data and reports remain local and are git-ignored.

## Important note

The proprietary dataset used to develop the reference models is not distributed with this project. The CSVs in `examples/csv/` are synthetic schema examples only.
