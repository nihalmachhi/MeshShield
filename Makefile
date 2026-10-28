.PHONY: install lint format typecheck test run bench site-install site-build

install:
	python -m pip install -e ".[dev]"

lint:
	python -m ruff check src tests scripts
	python -m ruff format --check src tests scripts

format:
	python -m ruff check --fix src tests scripts
	python -m ruff format src tests scripts

typecheck:
	python -m mypy src/meshshield

test:
	python -m pytest -q --cov=meshshield --cov-report=term-missing

run:
	meshshield serve

bench:
	python scripts/benchmark.py

site-install:
	npm ci --prefix site

site-build:
	npm run build --prefix site
