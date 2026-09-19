.PHONY: install test pipeline dbt dashboard up down

# dbt e streamlit sao invocados como modulo (python -m ...): no Python da
# Microsoft Store, os console scripts "dbt" e "streamlit" nao ficam no PATH.

install:
	pip install -r requirements.txt
	cd dbt && python -m dbt.cli.main deps

test:
	python -m pytest -v

pipeline:
	python -m src.pipeline

dbt:
	cd dbt && python -m dbt.cli.main build

dashboard:
	python -m streamlit run dashboard/app.py

up:
	docker compose up -d

down:
	docker compose down
