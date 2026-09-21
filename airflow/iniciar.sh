#!/usr/bin/env bash
# Partida do container do Airflow.
set -euo pipefail

# dbt/ e montado por cima da imagem, entao dbt_packages (gitignored) e recriado
# aqui, na partida, e nao no build.
python -m dbt.cli.main deps --project-dir /opt/airflow/dbt --profiles-dir /opt/airflow/dbt

airflow db migrate

# O modo standalone so cria o usuario admin, com senha aleatoria, quando ele
# ainda nao existe. Criando-o antes com a senha do .env, o login documentado
# funciona e continua valendo depois de recriar o container.
if airflow users list --output plain | awk 'NR > 1 {print $2}' | grep -qx admin; then
    airflow users reset-password --username admin --password "$AIRFLOW_ADMIN_PASSWORD"
else
    airflow users create --username admin --password "$AIRFLOW_ADMIN_PASSWORD" \
        --firstname Admin --lastname User --role Admin --email admin@example.com
fi

exec airflow standalone
