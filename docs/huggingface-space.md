# Hugging Face Space

This repository can run as a Gradio Hugging Face Space using the root `app.py`.

## What the Space does

- loads reference model artifacts
- runs the PayMind SDK directly in-process
- displays ranked demo recommendations
- explains the architecture
- points contributors to local training

The Space does **not** host proprietary training CSVs and does **not** run public CSV retraining.

## Required files

- `app.py`
- `frontend/app.py`
- `requirements.txt`
- `models/registry.json`
- reference model artifacts or a configured Hugging Face model repository

## Create a Space

1. Create a new Hugging Face Space.
2. Choose the `Gradio` SDK.
3. Push this repository contents.
4. Ensure `requirements.txt` is present.
5. Confirm the Space starts from `app.py`.

## Optional Hugging Face model repository configuration

`models/registry.json` can point to local artifacts or Hugging Face Hub artifacts.

If you want the Space repo to stay lighter, store `.cbm` and metadata files in a separate Hugging Face model repository and switch the manifest entries to:

- `source: "huggingface"`
- `repo_id`
- `revision`
- `filename`

## Optional environment variables / secrets

- `HUGGINGFACE_HUB_TOKEN`
  Use only if the model repository is private.
- `PAYMIND_HF_CACHE_DIR`
  Optional override for the local Hugging Face artifact cache directory.
- `GRADIO_SERVER_NAME`
  Optional Gradio host override for special environments.

If all artifacts are local, no Hugging Face secret is required.

## Loading behavior

- `source: "local"` loads the file directly from the repository or local filesystem.
- `source: "huggingface"` downloads the artifact through `huggingface_hub` into the local cache before CatBoost loads it.

Only model artifacts are loaded. Training CSVs are never downloaded or exposed.
