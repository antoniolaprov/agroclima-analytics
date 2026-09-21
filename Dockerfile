# Airflow + pipeline de ingestao/dbt
FROM apache/airflow:2.10.3-python3.12

USER root
RUN apt-get update && apt-get install -y --no-install-recommends git && rm -rf /var/lib/apt/lists/*
USER airflow

# requirements-airflow.txt (nao requirements.txt): so o necessario para
# ingestao e dbt. streamlit/plotly/statsmodels sao do dashboard e nao tem
# por que entrar aqui - alem de nao serem necessarios, arriscam colidir com
# as constraints internas do apache/airflow.
COPY requirements-airflow.txt /tmp/requirements-airflow.txt
RUN pip install --no-cache-dir -r /tmp/requirements-airflow.txt

ENV PYTHONPATH=/opt/airflow

# Criado como usuario airflow para que o volume nomeado herde o dono na primeira
# montagem; montado como root, o SQLite do Airflow nao conseguiria gravar.
RUN mkdir -p /opt/airflow/estado
