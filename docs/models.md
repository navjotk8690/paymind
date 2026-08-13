# Models

PayMind can load reference or user-retrained model artifacts from a local manifest.

## Supported model roles

- payment method candidate generator
- success / reliability model
- settlement P50 model
- settlement P90 model

## Reference models

Reference models are provided for demonstration and development only. Retrain PayMind on your own payment environment before real use.

They are not universally calibrated across merchants, geographies, currencies, or route configurations.

## Manifest

`models/registry.json` supports local files and optional Hugging Face Hub artifacts.

Example local artifact entry:

```json
{
  "source": "local",
  "local_path": "models/payment_method/payment_method_v1.cbm"
}
```

Example Hugging Face artifact entry:

```json
{
  "source": "huggingface",
  "repo_id": "your-org/paymind-reference-models",
  "revision": "main",
  "filename": "payment_method/payment_method_v1.cbm"
}
```

Metadata should remain public-safe and must not expose raw training records.
