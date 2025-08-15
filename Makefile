VENV?=.venv
PY?=python3

.PHONY: venv run worker up down test fmt lint

venv:
	$(PY) -m venv $(VENV)
	. $(VENV)/bin/activate && pip install -U pip wheel
	. $(VENV)/bin/activate && pip install -r requirements.txt

run:
	. $(VENV)/bin/activate && uvicorn app.main:app --host $${APP_HOST:-0.0.0.0} --port $${APP_PORT:-8080} --reload

worker:
	. $(VENV)/bin/activate && rq worker -u $${REDIS_URL:-redis://localhost:6379/0} ingest

up:
	docker compose up -d

down:
	docker compose down -v

test:
	. $(VENV)/bin/activate && pytest -q

fmt:
	. $(VENV)/bin/activate && ruff check --fix . && isort . && black .

lint:
	. $(VENV)/bin/activate && ruff check .

