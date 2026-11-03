.PHONY: install install-dev install-ml test pipeline dbt dashboard up down exportar-web web-dev web-build treinar treinar-forcar prever mlflow publicar-hf

# dbt e streamlit sao invocados como modulo (python -m ...): no Python da
# Microsoft Store, os console scripts "dbt" e "streamlit" nao ficam no PATH.

install:
	pip install -r requirements.txt
	cd dbt && python -m dbt.cli.main deps

install-ml:
	pip install -r requirements-ml.txt

install-dev:
	pip install -r requirements-dev.txt
	cd dbt && python -m dbt.cli.main deps

test:
	python -m pytest -v

pipeline:
	python -m src.pipeline

dbt:
	cd dbt && python -m dbt.cli.main build

dashboard:
	python -m streamlit run dashboard/app.py

treinar:
	python -m src.ml.treino

treinar-forcar:
	python -m src.ml.treino --forcar

prever:
	python -m src.ml.prever

mlflow:
	mlflow ui --backend-store-uri data/mlruns

# Uso: make publicar-hf REPO=usuario/agroclima-anomalia-rendimento (com HF_TOKEN no ambiente)
publicar-hf:
	python -m src.ml.publicar_hf --repo $(REPO)

exportar-web:
	python scripts/exportar_web.py

web-dev:
	cd web && npm run dev

web-build:
	cd web && npm run build

up:
	docker compose up -d

down:
	docker compose down
