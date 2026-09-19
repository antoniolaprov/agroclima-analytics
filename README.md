# AgroClima Analytics

Pipeline de dados que cruza clima e producao agricola no Brasil por estado.
Coleta dados do INMET e do IBGE, transforma em camadas Bronze/Silver/Gold e
disponibiliza em um dashboard interativo.

A pergunta que o projeto responde: como chuva e temperatura se relacionam com
a produtividade das principais culturas, por estado?

## O que o projeto faz

1. Baixa o historico horario das estacoes automaticas do INMET (2022-2026)
2. Busca area, producao e rendimento de soja, milho, cafe e cana no IBGE/SIDRA
3. Armazena os dados brutos em Parquet (Bronze)
4. Limpa e agrega para o nivel diario por estado com dbt (Silver)
5. Calcula KPIs, medias moveis e anomalias climaticas com dbt (Gold)
6. Exibe os resultados num dashboard Streamlit

O Airflow agenda o processo todo dia as 09h UTC (06h no horario de Brasilia).

## Tecnologias

- Python - ingestao
- dbt + DuckDB - transformacao, modelagem e testes
- Apache Airflow - agendamento
- Streamlit + Plotly - dashboard
- Docker - para rodar tudo junto

## Dados coletados

INMET (dados historicos das estacoes automaticas):

- temperatura, precipitacao, umidade e vento, por hora, agregados por estado

IBGE/SIDRA:

- PAM (tabela 5457): area plantada, area colhida, producao e rendimento anuais
- LSPA (tabela 6588): estimativas mensais da safra

## Como rodar

### Local (sem Docker)

```
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
cd dbt && python -m dbt.cli.main deps && cd ..

python -m src.pipeline
python -m streamlit run dashboard/app.py
```

Acesse: http://localhost:8501

A primeira execucao baixa cerca de 300 MB do INMET e leva alguns minutos. As
seguintes verificam o ETag do arquivo e so baixam o que mudou.

Para avaliar o projeto sem esperar esse download, rode
`python scripts/seed_bronze_dev.py` antes: ele grava uma camada Bronze
fabricada e pequena, no mesmo formato da ingestao real, o suficiente para
rodar o dbt (`cd dbt && python -m dbt.cli.main build`) e abrir o dashboard
com dados.

`dbt` e `streamlit` sao chamados como modulo (`python -m ...`) porque, no
Python distribuido pela Microsoft Store, os console scripts desses pacotes
nao ficam expostos no PATH. Se o seu Python nao tiver essa limitacao, os
comandos `dbt` e `streamlit run` diretos tambem funcionam.

O Airflow nao roda nativamente no Windows; use o Docker para a parte de
agendamento.

### Com Docker (inclui Airflow)

```
cp .env.example .env
docker compose up -d
```

- Dashboard: http://localhost:8501
- Airflow: http://localhost:8080 (usuario e senha em `.env`, padrao admin/admin)

O container do dashboard so mostra dados depois que o pipeline (local ou via
DAG do Airflow) gerar `data/warehouse.duckdb` - os dois servicos compartilham
o diretorio `data/` como volume. Para popular rapido sem esperar o
agendamento, rode o pipeline localmente (secao anterior) antes de subir o
Docker, ou dispare a DAG `agroclima_pipeline` manualmente pela UI do Airflow.

## Estrutura

- `src/ingestion` - clientes das APIs, gravam Parquet em `data/bronze`
- `scripts/seed_bronze_dev.py` - gera uma Bronze fake para desenvolvimento local
- `dbt/models/staging` - limpeza e padronizacao (Silver)
- `dbt/models/marts` - KPIs e cruzamentos (Gold)
- `dashboard` - aplicacao Streamlit
- `airflow/dags` - agendamento
- `requirements.txt` - dependencias para rodar local e o dashboard
- `requirements-airflow.txt` - subconjunto usado na imagem do Airflow (sem
  streamlit/plotly/statsmodels, que sao so do dashboard e podem colidir com
  as constraints do apache/airflow)

## Limitacoes conhecidas

- A media climatica por estado nao e ponderada por area: estados grandes tem
  cobertura desigual de estacoes. O campo `n_estacoes` fica visivel no
  dashboard para o leitor julgar cada ponto.
- A API horaria do INMET (`apitempo`) esta fechada e retorna 204; o projeto
  usa os arquivos anuais de dados historicos, atualizados a cada ~90 dias.

## Fontes

- [INMET Dados Historicos](https://portal.inmet.gov.br/dadoshistoricos)
- [IBGE API de agregados](https://servicodados.ibge.gov.br/api/docs/agregados?versao=3)
