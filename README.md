---
title: PayMind
emoji: 💳
colorFrom: blue
colorTo: indigo
sdk: gradio
app_file: app.py
pinned: false
license: gpl-3.0
short_description: Open-source payment route intelligence
---

# PayMind
# PayMind

[![Hugging Face Space](https://img.shields.io/badge/Hugging%20Face-Live%20Demo-FFD21E?logo=huggingface&logoColor=black)](https://huggingface.co/spaces/navk8690/paymind)

Open-source payment route intelligence for smarter route selection.

## 🚀 Live Demo

Try **PayMind** directly in your browser using the interactive Gradio demo hosted on Hugging Face Spaces.

👉 **[Launch PayMind Live Demo](https://huggingface.co/spaces/navk8690/paymind)**

> **Note:** The demo uses synthetic/reference data and reference models to demonstrate PayMind's payment route intelligence workflow. Results do not represent actual payment-provider performance.

**Open-source payment intelligence for smarter payment-route decisions.**

PayMind is a fork-friendly payment intelligence engine that evaluates eligible payment routes using machine learning, settlement intelligence, configurable fee logic, and deterministic ranking.

It is designed to answer a simple question:

> **Of the payment routes available for this transaction, which route provides the strongest combination of relevance, reliability, settlement performance, and cost?**

PayMind is **not a payment gateway**. It does not execute payments, hold funds, require customer payment credentials, or require a database simply to evaluate a transaction.

The project is designed to run inside your own environment and to be retrained using your own payment data.

> **Demo notice:** The public demo, synthetic datasets, and bundled reference models are intended for demonstration and development. Reference model outputs do not represent actual payment-provider performance.

---

## Core Intelligence Components

The PayMind reference implementation combines machine-learning predictions with deterministic payment decision logic.

- **Candidate Generator** — CatBoost multiclass route-relevance model
- **Reliability Engine** — CatBoost binary transaction-success model
- **Settlement Intelligence** — CatBoost P50/P90 arrival-time models
- **Eligibility Engine** — deterministic runtime route filtering
- **Fee Engine** — deterministic configurable fee calculation
- **Ranking Engine** — weighted final route decision engine
- **Feature Builder** — canonical transaction-to-model feature transformation
- **Model Registry** — loading and versioning layer for model artifacts

A useful distinction in the architecture is:

> **CatBoost predicts. PayMind decides.**

The ML models produce predictive signals. PayMind's deterministic decision layer determines how those signals, route availability, and commercial inputs contribute to the final recommendation.

---

## Decision Flow

```text
Transaction
    │
    ▼
Feature Builder
    │
    ▼
Eligibility
    │
    ▼
Candidate Generator
    │
    ▼
Reliability Engine
    │
    ▼
Settlement Intelligence
    │
    ▼
Fee Engine
    │
    ▼
Ranking Engine
    │
    ▼
Ranked Recommendation
```

Each stage has a separate responsibility so that individual components can be replaced, retrained, or extended without rewriting the entire engine.

---

# Models

PayMind currently uses **CatBoost** for the machine-learning components in the reference implementation.

The public reference model set contains four model artifacts across three modelling responsibilities.

## Candidate Generator

**Technology:** CatBoost  
**Model type:** Multiclass classification  
**Purpose:** Payment-route relevance

The Candidate Generator estimates which payment methods are most relevant for the current transaction context.

It produces a probability distribution across candidate payment methods.

Example:

```text
Paypal     0.57
Revolut    0.36
Stripe     0.01
...
```

These probabilities represent **candidate relevance**, not the final PayMind recommendation.

Candidate relevance becomes one signal in the downstream ranking process.

Conceptually, the model answers:

> Which payment routes most closely match this transaction context?

---

## Reliability Engine

**Technology:** CatBoost  
**Model type:** Binary classification  
**Purpose:** Transaction-success prediction

The Reliability Engine estimates the probability that a transaction will succeed through each candidate payment route.

Example:

```text
Paypal     success_probability = 0.81
Revolut    success_probability = 0.81
Stripe     success_probability = 0.30
```

This is deliberately separate from candidate relevance.

A payment method may be highly relevant to a transaction while another route may have a stronger predicted probability of successful processing.

The Reliability Engine therefore answers:

> Given this transaction and this route, how likely is the transaction to succeed?

---

## Settlement Intelligence

**Technology:** CatBoost  
**Model type:** Quantile/regression modelling  
**Purpose:** Arrival/settlement-time prediction

Settlement Intelligence consists of two models:

```text
P50 Settlement Model
P90 Settlement Model
```

### P50

P50 represents the median expected arrival time.

Approximately half of comparable observations are expected to arrive within this estimate.

It provides PayMind with a view of **typical settlement behaviour**.

### P90

P90 provides a more conservative settlement estimate.

Approximately 90% of comparable observations are expected to arrive within this estimate.

It gives the ranking engine information about slower-tail settlement behaviour rather than relying only on the median.

Using both P50 and P90 becomes particularly useful when the training environment contains payment methods with materially different settlement characteristics, including instant payment methods and slower bank-payment routes.

---

# Deterministic Intelligence

Not every PayMind component is machine learned.

This is intentional.

Route availability, pricing, business constraints, and final decision policy should not necessarily be learned from historical transactions.

---

## Eligibility Engine

**Type:** Deterministic runtime filtering

The Eligibility Engine determines which routes are allowed to participate in the recommendation.

Eligibility can consider information such as:

- merchant-available routes
- transaction type
- currency
- country
- IP country
- jurisdiction
- application/channel
- cross-border context
- connector-specific restrictions

A route that is unavailable or ineligible should not win simply because a model assigns it a high score.

Eligibility therefore happens before final ranking.

---

## Fee Engine

**Type:** Deterministic configuration-driven calculation

The Fee Engine estimates the commercial cost associated with each candidate route.

The reference implementation supports:

- percentage fees
- fixed fees
- FX percentage fees
- total estimated fee
- effective fee rate

Example configuration:

```json
{
  "stripe": {
    "percentage": 1.5,
    "fixed": 0.30,
    "fx_percentage": 0.0
  }
}
```

For a transaction, the Fee Engine can derive values such as:

```text
percentage_fee
fixed_fee
fx_fee
total_fee
effective_fee_rate
```

The current configuration-driven implementation is intentionally replaceable.

A real integration can supply pricing dynamically through connector or route configuration without retraining the machine-learning models.

---

## Ranking Engine

**Type:** Deterministic weighted decision engine

The Ranking Engine combines PayMind's predictive and commercial signals into the final route score.

Conceptually:

```text
Candidate Relevance
        +
Predicted Reliability
        +
Settlement Performance
        +
Fee Performance
        =
Final Route Score
```

The individual signals are normalized and combined using configurable ranking weights.

This separation allows model behaviour and business decision policy to evolve independently.

The output can include readable recommendation reasons such as:

```text
HIGH_SUCCESS_PROBABILITY
FAST_EXPECTED_SETTLEMENT
COMPETITIVE_FEE
HIGH_CANDIDATE_RELEVANCE
```

The result is a ranked set of routes rather than a raw model prediction.

---

## Feature Builder

PayMind derives model-ready features from the canonical transaction context.

Depending on the model configuration, derived features can include concepts such as:

```text
timestamp
hour
day_of_week
is_weekend
month
quarter
cross-border context
amount transformations
```

This keeps feature engineering inside PayMind rather than requiring every connector to reproduce model-specific transformations.

---

## Model Registry

Model artifacts are loaded through the PayMind Model Registry.

The reference model structure is conceptually:

```text
Model Registry
│
├── Candidate Generator
│   └── CatBoost multiclass model
│
├── Reliability Engine
│   └── CatBoost binary classifier
│
└── Settlement Intelligence
    ├── CatBoost P50 model
    └── CatBoost P90 model
```

The current reference artifacts are:

```text
models/
├── payment_method/
│   └── payment_method_v1.cbm
│
├── success/
│   └── success_v1.cbm
│
└── arrival/
    ├── arrival_p50_v1.cbm
    └── arrival_p90_v1.cbm
```

The registry allows the runtime to keep model loading separate from the decision engine.

Model metadata can describe information such as:

- model version
- training rows
- feature definitions
- evaluation metrics
- artifact location
- model source
- optional Hugging Face model repository/revision

Reference artifacts can be bundled locally or distributed separately through a model repository.

---

# What PayMind Does

PayMind can:

- accept a canonical transaction request
- derive model features
- filter eligible payment routes
- rank candidate route relevance
- predict transaction success probability
- estimate P50 settlement time
- estimate P90 settlement time
- calculate configured fee impact
- combine signals through weighted ranking
- return ranked payment-route recommendations
- provide readable reasons for the recommendation

PayMind therefore goes beyond asking:

> Which payment method is available?

The decision problem becomes:

> Which eligible route currently provides the best combination of predicted performance and commercial characteristics for this transaction?

---

# What PayMind Does Not Do

PayMind:

- is **not** a payment gateway
- is **not** a payment processor
- is **not** a hosted payment orchestration SaaS
- does not execute payments
- does not hold or move funds
- does not require customer payment credentials
- does not require persisted raw transaction data
- does not ship proprietary production datasets
- does not provide hosted public model training through the demo Space

PayMind is intended to operate as an **intelligence and decision layer** alongside an existing payment infrastructure.

---

# Technology Stack

The current open-source reference implementation uses:

| Component | Technology |
|---|---|
| Machine learning | **CatBoost** |
| Candidate modelling | **CatBoost multiclass classification** |
| Reliability modelling | **CatBoost binary classification** |
| Settlement modelling | **CatBoost P50/P90 models** |
| Data processing / inspection | **Python / DuckDB** |
| SDK | **Python** |
| API | **FastAPI** |
| Validation | **Pydantic** |
| Demo interface | **Gradio** |
| Model artifacts | **CatBoost `.cbm`** |
| Fee configuration | **JSON** |
| Testing | **pytest** |
| Demo hosting | **Hugging Face Spaces compatible** |
| Model distribution | **Local registry / optional Hugging Face Hub** |

The architecture intentionally keeps these layers independent.

A fork can replace the modelling implementation while continuing to use PayMind's:

- canonical transaction interface
- feature pipeline
- eligibility logic
- fee engine
- ranking architecture
- SDK
- API
- connector interfaces

---

# Reference Models

The public PayMind demo uses reference model artifacts so that the complete decision pipeline can be explored without access to a production payment environment.

The reference model set includes:

```text
Candidate Generator
└── payment_method_v1.cbm

Reliability Engine
└── success_v1.cbm

Settlement Intelligence
├── arrival_p50_v1.cbm
└── arrival_p90_v1.cbm
```

These are **reference/demo models**.

They exist to demonstrate:

- multiclass route relevance
- route-specific reliability prediction
- P50/P90 settlement modelling
- fee-aware ranking
- runtime eligibility
- end-to-end recommendation generation

They should **not** be interpreted as evidence that one named payment provider performs better or worse than another in the real world.

For actual use, retrain PayMind using data representative of your own payment environment.

---

# Synthetic Data and Data Policy

The public PayMind project is designed to remain safe for open-source distribution.

The public example/training material is synthetic and intended to demonstrate the architecture and expected schemas.

Safe example CSVs live under:

```text
examples/csv/
```

Working directories such as:

```text
data/training/
data/processed/
data/splits/
data/reports/
```

are kept empty by default except where `.gitkeep` is required and are excluded from normal source-control usage.

PayMind does **not** require users to publish their training data.

To retrain locally, provide your own datasets under:

```text
data/training/
```

Production transaction CSVs should never be committed to the public repository.

---

# Repository Contents

The project is structured roughly as:

```text
paymind/
│
├── app.py
├── frontend/
│   └── app.py
│
├── src/
│   └── paymind/
│
├── models/
│
├── config/
│
├── examples/
│   └── csv/
│
├── data/
│
├── docs/
│
├── scripts/
│   └── train_all.py
│
├── tests/
│
├── pyproject.toml
├── README.md
└── LICENSE
```

Important components include:

- `app.py` — Hugging Face Space / demo entrypoint
- `frontend/app.py` — interactive Gradio interface
- `src/paymind/` — core SDK, models and decision engine
- `models/` — reference CatBoost artifacts and registry
- `config/` — runtime configuration including fee configuration
- `examples/csv/` — safe synthetic schema examples
- `scripts/train_all.py` — end-to-end local model training pipeline
- `docs/` — architecture, training, models, schemas and connector documentation
- `tests/` — automated tests

---

# Quick Start

Clone the repository:

```bash
git clone https://github.com/navjotk8690/paymind.git
cd paymind
```

Create a virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Upgrade pip and install PayMind:

```bash
python3 -m pip install --upgrade pip
python3 -m pip install -e '.[space,training]'
```

---

# Run the Demo

Start the Gradio interface:

```bash
python3 app.py
```

The demo calls PayMind directly in-process.

A separate API server is not required.

The interface allows you to modify transaction context, select available routes, and inspect the resulting recommendation.

---

# Run the FastAPI Service

PayMind can also operate as a standalone API:

```bash
python3 -m uvicorn paymind.api.app:app \
  --host 127.0.0.1 \
  --port 8080
```

Available endpoints:

```text
GET  /health
GET  /models
POST /evaluate
```

---

# SDK Usage

PayMind can be embedded directly into another Python application.

```python
from pathlib import Path
import json

from paymind import PayMind

engine = PayMind()

payload = json.loads(
    Path("examples/request.json").read_text()
)

result = engine.evaluate(payload)

print(
    result.model_dump_json(indent=2)
)
```

The SDK allows the core intelligence engine to operate without requiring either the FastAPI or Gradio layer.

---

# Train Your Own Models

PayMind is designed to be **forked and retrained**.

The bundled models provide a working reference implementation. They are not intended to permanently define the behaviour of a PayMind installation.

Local training expects your own CSVs at:

```text
data/training/payment_method.csv
data/training/success.csv
data/training/arrival.csv
```

Run the complete training pipeline with:

```bash
python3 scripts/train_all.py
```

The pipeline covers:

```text
Input inspection
        ↓
Cleaning
        ↓
Chronological splitting
        ↓
Class-policy checks
        ↓
Feature validation
        ↓
Candidate Generator training
        ↓
Reliability Engine training
        ↓
Arrival-target inspection
        ↓
P50 settlement training
        ↓
P90 settlement training
        ↓
Model evaluation
        ↓
Tests
```

Failures stop the pipeline immediately.

This allows contributors to replace the reference models with models learned from their own payment environment.

Exact input schemas are documented in:

```text
docs/data-schemas.md
```

---

# Training Data

Three canonical datasets are used by the reference training pipeline.

## Payment Method Dataset

```text
payment_method.csv
```

Used to train the **Candidate Generator**.

The target represents the payment method/route associated with the historical transaction context.

---

## Success Dataset

```text
success.csv
```

Used to train the **Reliability Engine**.

The target represents transaction success/failure for the corresponding payment context and route.

---

## Arrival Dataset

```text
arrival.csv
```

Used to train **Settlement Intelligence**.

The arrival/settlement duration is used to train the P50 and P90 models.

---

# Example CSVs

Synthetic schema examples are provided under:

```text
examples/csv/payment_method_template.csv
examples/csv/success_template.csv
examples/csv/arrival_template.csv
```

These files demonstrate the expected data structure.

They are **not intended to provide production-quality training performance**.

Users should replace them with data representative of their own payment environment when training real models.

---

# Forking PayMind

The intended open-source workflow is:

```text
Fork PayMind
      │
      ▼
Provide your own payment history
      │
      ▼
Run the training pipeline
      │
      ▼
Evaluate model performance
      │
      ▼
Configure route fees
      │
      ▼
Load your model artifacts
      │
      ▼
Run PayMind in your environment
      │
      ▼
Connect the recommendation
to your payment infrastructure
```

The core architecture is intentionally modular.

A fork can customize:

- model artifacts
- model features
- eligibility policies
- fee configuration
- ranking weights
- payment-route definitions
- connector integrations
- API integration

without turning PayMind itself into a payment processor.

---

# Hugging Face

PayMind is designed to support two separate Hugging Face use cases.

## Model Repository

Reference CatBoost model artifacts can be distributed through the **Hugging Face Hub**.

This keeps model distribution separate from the source repository when desired.

## Gradio Space

The root:

```text
app.py
```

acts as the Hugging Face Space entrypoint.

The public Space is intended to:

- demonstrate the PayMind decision pipeline
- load reference models
- allow users to experiment with transaction scenarios
- expose recommendation reasoning
- explain the model architecture

The Space does **not**:

- expose production training data
- require private payment data
- execute payments
- move funds
- provide hosted public model retraining

The Space is an interactive demonstration of the open-source connector.

Deployment documentation is available in:

```text
docs/huggingface-space.md
```

---

# Privacy and Safety

PayMind follows a **bring-your-own-data** model.

The public project is designed so that:

- production training CSVs are not required in the repository
- processed private datasets do not need to be committed
- train/validation/test splits do not need to be published
- raw transaction payloads do not need to be persisted by default
- payment credentials remain outside PayMind
- payment execution remains outside PayMind

Reference models and synthetic datasets should be treated as development and demonstration assets rather than production-calibrated truth.

Production users are responsible for validating models, policies, fees, eligibility rules, and integrations against their own payment environment.

---

# Verification

Run the automated test suite:

```bash
python3 -m pytest -q
```

Tests should be run after changes to:

- feature engineering
- models
- training
- eligibility
- fee configuration
- ranking
- API schemas
- connectors

---

# Documentation

Additional project documentation:

- `docs/architecture.md` — system architecture and decision flow
- `docs/training.md` — model-training workflow
- `docs/data-schemas.md` — canonical training CSV schemas
- `docs/models.md` — model architecture and artifacts
- `docs/connectors.md` — connector and integration concepts
- `docs/huggingface-space.md` — demo deployment

---

# Contributing

PayMind is intended to be forked, experimented with, and improved.

Contributions can include:

- new model approaches
- additional payment features
- alternative settlement models
- improved ranking strategies
- connector implementations
- eligibility policies
- evaluation tooling
- documentation
- synthetic datasets
- testing and benchmarking

When contributing datasets or model artifacts, ensure that you have the right to distribute them and that they do not contain private or proprietary payment data.

---

# License

PayMind is released under the **GNU General Public License v3.0 (GPL-3.0)**.

You may use, study, modify, and redistribute PayMind under the terms of the GPL-3.0.

If you distribute modified versions or derivative works covered by the GPL, they must also be distributed under GPL-compatible terms with the corresponding source code made available as required by the license.

See [`LICENSE`](LICENSE) for the full license text.

---

## Disclaimer

PayMind is an experimental open-source payment intelligence project.

Reference predictions, synthetic datasets, model metrics, settlement estimates, fee calculations, and recommendations are provided for demonstration and development purposes.

They should not be interpreted as guarantees of payment-provider performance, settlement outcomes, transaction success, or commercial cost.