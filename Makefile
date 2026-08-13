.PHONY: install test api demo lint docker

install:
	python3 -m pip install -e ".[all]"

test:
	python3 -m pytest -q

api:
	python3 -m uvicorn paymind.api.app:app --host 127.0.0.1 --port 8080

demo:
	python3 frontend/app.py

lint:
	python3 -m ruff check src tests frontend

docker:
	docker build -t navcore-paymind:v1 .
