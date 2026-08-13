# Models

`models/` contains reference artifacts for the open-source demo and local development experience.

These reference models are provided for demonstration and development only. Retrain PayMind on your own payment environment before real use.

The proprietary dataset used to develop the reference models is not distributed with this project. No raw transaction data, customer data, or private training CSVs are included here.

You have two supported ways to supply model artifacts:

1. Keep local artifacts under `models/` and point the manifest at them.
2. Configure `models/registry.json` to download reference artifacts from a Hugging Face model repository.

PayMind never downloads or exposes training CSVs. Only model weights and safe metadata are loaded.
