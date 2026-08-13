# Architecture

PayMind is a self-hosted payment intelligence connector, not a payment gateway.

## Request flow

1. `EvaluateRequest`
2. candidate generator
3. reliability model
4. settlement intelligence
5. fee service
6. ranking engine
7. `EvaluateResponse`

## Runtime components

- `paymind.sdk.PayMind`
- `paymind.models.registry.ModelRegistry`
- `paymind.models.candidate_generator.CandidateGenerator`
- `paymind.models.reliability_engine.ReliabilityEngine`
- `paymind.models.settlement_engine.SettlementEngine`
- `paymind.fees.service.FeeService`
- `paymind.ranking.decision_engine.DecisionEngine`

## Deployment model

- Run inside the user's own environment.
- Use the SDK directly, the FastAPI app, or a custom connector wrapper.
- No database is required for basic inference.
- No telemetry, billing, authentication, or hosted persistence is required.

## Privacy model

- PayMind does not need to store transaction data.
- Proprietary training data is not distributed.
- The Hugging Face Space only serves as an interactive reference demo.
