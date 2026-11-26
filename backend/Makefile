install:
	pip install -e ".[dev]"

api:
	uvicorn app.main:app --reload --host 127.0.0.1 --port 8000

worker:
	python scripts/run_worker.py

test:
	pytest -q

check:
	python -m compileall -q app scripts
	ruff check .
