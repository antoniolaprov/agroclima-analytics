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

# Criado como usuario airflow e gravavel pelo grupo root, para que o volume
# nomeado herde essas permissoes na primeira montagem: o container roda com
# grupo 0 e, no Linux, com o UID do usuario do host.
RUN mkdir -p /opt/airflow/estado && chmod g+rwx /opt/airflow/estado
