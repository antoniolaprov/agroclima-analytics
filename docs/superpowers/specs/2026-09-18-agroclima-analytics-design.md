# AgroClima Analytics — Design

Data: 2026-09-18
Status: aprovado para planejamento de implementação

## 1. Objetivo

Pipeline de dados que cruza clima e produção agrícola no Brasil por UF.
Coleta dados meteorológicos do INMET e dados de safra do IBGE/SIDRA,
transforma em camadas Bronze/Silver/Gold e disponibiliza em um dashboard
interativo.

A pergunta que o projeto responde: **como chuva e temperatura se relacionam
com a produtividade das principais culturas, por estado?**

Projeto irmão do [finbrasil-analytics](https://github.com/antoniolaprov/finbrasil-analytics),
com a mesma stack. A diferença deliberada de arquitetura está na seção 3.

## 2. Escopo

**Dentro do escopo:**

- Granularidade geográfica: UF (27 unidades federativas)
- Culturas: soja, milho, café e cana-de-açúcar
- Histórico: 5 anos de clima (2022–2026)
- Dashboard com 4 páginas
- Orquestração diária via Airflow
- Execução local (sem Docker) e via `docker compose`

**Fora do escopo:**

- Granularidade municipal (cobertura irregular de estações e complexidade
  geoespacial de associar estação a município)
- Previsão ou modelagem preditiva de safra
- Culturas além das quatro listadas
- Autenticação no dashboard

## 3. Decisão de arquitetura: Python ingere, dbt transforma

No FinBrasil, as camadas Silver e Gold são classes Python
(`BronzeToSilver`, `SilverToGold`), e o dbt existe ao lado sem ser executado
pelo pipeline nem pela DAG. Os modelos dbt são decorativos.

Aqui a divisão é estrita:

| Camada | Responsável | Motivo |
|---|---|---|
| Bronze | Python | Falar HTTP, descompactar ZIP, parsear CSV |
| Silver | dbt | Limpeza e padronização são SQL declarativo |
| Gold | dbt | Agregação e janelas são SQL declarativo |
| Qualidade | dbt tests | Portão único, não dois limiares divergentes |

Consequências:

- Não existem `src/transformation/` nem `src/warehouse/`.
- O portão de qualidade é o `dbt build`. O FinBrasil tinha dois limiares
  inconsistentes (70% em `pipeline.py`, 80% na DAG); aqui não há limiar
  percentual — um teste que falha derruba a execução.
- A lógica de negócio fica versionada em SQL legível, com lineage e docs
  gerados pelo dbt.

## 4. Fontes de dados

Tudo nesta seção foi verificado em 2026-09-18 com requisições reais.

### 4.1 INMET — clima

**Catálogo de estações** — `GET https://apitempo.inmet.gov.br/estacoes/T`

- 674 estações automáticas, JSON, sem token
- Campos relevantes: `CD_ESTACAO`, `SG_ESTADO` (UF), `DC_NOME`,
  `VL_LATITUDE`, `VL_LONGITUDE`, `VL_ALTITUDE`, `CD_SITUACAO`,
  `DT_INICIO_OPERACAO`, `DT_FIM_OPERACAO`
- Como `SG_ESTADO` já traz a UF, **não é necessário seed de estação→UF**

**Dados horários** — `GET https://portal.inmet.gov.br/uploads/dadoshistoricos/{ano}.zip`

A API JSON horária (`apitempo.inmet.gov.br/estacao/{ini}/{fim}/{cod}`) está
fechada: retorna `204 No Content` para todas as combinações testadas de
estação e ano. A rota `/condicao/capitais/{data}` cobre só 28 capitais e
devolve `*` nos valores. Portanto a única fonte aberta viável é o ZIP anual.

- ~61 MB por ano; 639 CSVs no ZIP de 2026 (um por estação)
- Nome do arquivo: `INMET_{REGIAO}_{UF}_{CODIGO}_{NOME}_{DD-MM-AAAA}_A_{DD-MM-AAAA}.CSV`
- Estrutura do CSV:
  - 8 linhas de metadados (região, UF, estação, código WMO, lat, lon,
    altitude, data de fundação), cabeçalho na linha 9
  - separador `;`, vírgula decimal, encoding `latin1`
  - colunas: precipitação horária (mm), pressão, radiação global,
    temperatura (bulbo seco / orvalho / máx / mín), umidade relativa,
    vento (direção, rajada, velocidade)
  - data `AAAA/MM/DD`, hora no formato `0000 UTC`
- **Valores ausentes: campo vazio** (7,4% dos campos na amostra inspecionada).
  Não há `-9999` nem `null` no arquivo verificado. O parser trata vazio,
  `-9999` e `9999` por precaução.
- Atualização a cada ~90 dias: o ZIP de 2026 termina em 31-08-2026

### 4.2 IBGE SIDRA — safra

Base: `https://servicodados.ibge.gov.br/api/v3/agregados`

Padrão: `/{tabela}/periodos/{periodos}/variaveis/{vars}?localidades=N3[all]&classificacao={cls}[{codigos}]`

**PAM — tabela 5457** (produção consolidada, anual 1974–2025, nível N3)

- Variáveis: `8331` área plantada, `216` área colhida, `214` quantidade
  produzida, `112` rendimento médio, `215` valor da produção
- Classificação `c782`: soja `40124`, milho em grão `40122`,
  café total `40139`, cana-de-açúcar `40106`

**LSPA — tabela 6588** (estimativa mensal, 2006-09 a 2026-08, nível N3)

- Variáveis: `109` área plantada, `216` área colhida, `35` produção,
  `36` rendimento médio
- Classificação `c48`: soja `39443`, café total `40527`, cana `39456`,
  milho **1ª safra `39441` e 2ª safra `39442`**

**Ponto de atenção — milho.** O LSPA separa milho em 1ª e 2ª safra; o PAM
tem um único "Milho (em grão)". A `dim_cultura` reconcilia isso: cada linha
LSPA carrega `cultura_id` (milho) e `safra_ciclo` (1 ou 2), e a comparação
com o PAM soma os dois ciclos.

Consulta de validação executada (soja, 2024): MT 38.396.410 t (3.109 kg/ha),
PR 18.689.393 t (3.240 kg/ha), RS 18.247.609 t (2.806 kg/ha).

## 5. Camadas

### 5.1 Bronze (Python)

Parquet em `data/bronze/`, sem transformação além do parse. Toda tabela
recebe `_ingested_at` e `_source_url`.

| Tabela | Origem | Estratégia |
|---|---|---|
| `estacoes` | `/estacoes/T` | carga completa a cada execução |
| `clima_horario` | ZIP anual | condicional, particionado por ano |
| `pam` | SIDRA 5457 | carga completa (tabela pequena) |
| `lspa` | SIDRA 6588 | carga completa restrita aos anos do clima (a série inteira passa do limite de valores por consulta do SIDRA e ele responde 500) |

**Ingestão condicional do ZIP.** Antes de baixar, o ingestor faz `HEAD` no
ZIP e compara `ETag`/`Last-Modified` com o valor gravado em
`data/bronze/_manifest.json`. Se não mudou, pula o download. Assim a DAG
roda todo dia sem reprocessar 61 MB à toa.

Anos carregados: 2022 a 2026 (~300 MB de ZIP).

### 5.2 Silver (dbt)

Limpeza e padronização. Materialização: view, exceto `stg_clima_diario`
(table, por volume).

- `stg_estacoes` — tipos, filtro de estações operantes, UF normalizada
- `stg_clima_horario` — vírgula decimal para float, ausentes para NULL,
  timestamp UTC montado a partir de data + hora
- `stg_clima_diario` — agrega horário para diário por estação:
  temperatura média/máx/mín, precipitação somada, umidade média. Faz join
  com `stg_estacoes` para carregar `uf`, que é a chave usada pela camada
  Gold. Um dia só entra se tiver no mínimo 18 das 24 horas; abaixo disso é
  descartado para não enviesar a média.
- `stg_pam`, `stg_lspa` — tipos, código de UF, nome de cultura normalizado
- `dim_uf`, `dim_cultura` — dimensões

### 5.3 Gold (dbt)

Materialização: table.

- **`gold_clima_uf_mensal`** — clima agregado por UF e mês: temperatura
  média/máx/mín, precipitação acumulada, dias sem chuva, número de
  estações que contribuíram, média móvel de 3 meses e anomalia de
  temperatura e chuva contra a média histórica do mesmo mês.
- **`gold_safra_uf`** — área, produção, produtividade e variação ano contra
  ano por UF e cultura, a partir do PAM.
- **`gold_clima_safra`** — junta as duas anteriores na janela do ciclo de
  cada cultura, com chuva acumulada e temperatura média do ciclo ao lado da
  produtividade. Base da análise de correlação.

**Agregação estação → UF.** A média por UF é simples entre estações, não
ponderada por área. É uma simplificação assumida: estados grandes têm
cobertura desigual (RS tem 98 estações, vários estados têm menos de 10). O
campo `n_estacoes` fica exposto no dashboard para o leitor julgar a
confiabilidade de cada célula.

**Janela de ciclo por cultura.** Definida em um seed
`seeds/ciclo_cultura.csv` com mês de plantio e de colheita por cultura e
região, para que a regra fique explícita e editável em vez de enterrada em
SQL.

## 6. Qualidade

Testes dbt, sem limiar percentual:

- `not_null` e `unique` nas chaves de todas as camadas
- `relationships` de `stg_clima_diario.uf` para `dim_uf`
- `accepted_values` para UF (as 27) e para cultura (as 4)
- faixas plausíveis: temperatura entre -10 e 50 °C, precipitação >= 0,
  umidade entre 0 e 100, produtividade > 0
- teste singular: a soma de milho 1ª + 2ª safra do LSPA não pode divergir
  mais de 5% do milho do PAM no total nacional do mesmo ano. Por UF a
  comparação não serve: em estados de produção pequena a estimativa da LSPA e
  o censo da PAM divergem de verdade (mais de 100% no AM em 2022), enquanto
  no total do país ficaram a menos de 1% em 2022-2025

Um teste que falha derruba o `dbt build` e a DAG. As tabelas Gold da
execução anterior permanecem no DuckDB, então o dashboard continua servindo
o último estado bom.

Os ingestores validam apenas o formato da resposta antes de gravar Bronze:
colunas esperadas presentes e resposta não vazia.

## 7. Orquestração

DAG `agroclima_pipeline`, diária às 06h BRT (09h UTC), `max_active_runs=1`,
2 tentativas com 5 minutos de intervalo.

```
start → [ingest_inmet_estacoes, ingest_inmet_clima, ingest_sidra] → dbt_build → notify → end
```

`ingest_inmet_clima` é condicional (seção 5.1): na maioria das execuções
detecta que o ZIP não mudou e termina em segundos. O `dbt_build` roda
sempre, porque o SIDRA pode ter mudado.

`dbt_build` é um `PythonOperator` que chama `rodar_dbt` (a mesma função
usada pelo pipeline local), que invoca `dbt build` via subprocess. Preferido
a um `BashOperator` porque reaproveita a invocação do dbt já centralizada em
`src/pipeline.py` (mesmo `sys.executable -m dbt.cli.main`, mesmo cwd), em
vez de duplicar esse comando no DAG.

## 8. Dashboard

Streamlit + Plotly, 4 páginas em `dashboard/views/`, com filtros de UF,
cultura e período.

1. **Visão geral** — KPIs e gráfico de barras horizontais de produção por
   UF. Um mapa coroplético do Brasil com a malha GeoJSON do IBGE ficou como
   trabalho futuro; o gráfico de barras cobre a mesma leitura (comparar UFs)
   sem a complexidade extra de buscar e cachear a malha
2. **Clima** — séries de temperatura e precipitação, anomalia contra a
   média histórica, média móvel
3. **Safra** — área, produção, produtividade e variação anual por cultura
4. **Clima × Safra** — dispersão de chuva ou temperatura contra
   produtividade, com coeficiente de correlação por cultura

**Concorrência no DuckDB.** O DuckDB aceita um escritor por vez entre
processos. Se o dbt estiver escrevendo durante a janela das 06h, o
dashboard pode falhar ao abrir conexão. Mitigação: o dashboard abre conexão
somente-leitura, curta, por consulta, com `st.cache_data` e uma nova
tentativa em caso de lock. A janela de escrita é de poucos segundos.

## 9. Estrutura do repositório

```
agroclima-analytics/
├── src/
│   ├── __init__.py
│   ├── pipeline.py              ingestão + subprocess dbt build
│   └── ingestion/
│       ├── base.py              retry, logging, escrita Parquet
│       ├── inmet_api.py         estações + ZIP condicional
│       └── sidra_api.py         PAM + LSPA
├── dbt/
│   ├── dbt_project.yml
│   ├── profiles.yml
│   ├── seeds/ciclo_cultura.csv
│   ├── models/staging/          stg_*.sql, dim_*.sql, sources.yml, schema.yml
│   ├── models/marts/            gold_*.sql, schema.yml
│   └── tests/                   testes singulares
├── airflow/dags/agroclima_pipeline_dag.py
├── dashboard/
│   ├── app.py
│   ├── views/                   overview.py, clima.py, safra.py, clima_safra.py
│   ├── Dockerfile
│   └── .streamlit/config.toml
├── tests/
│   ├── fixtures/                amostras de CSV INMET e JSON SIDRA
│   ├── test_inmet_api.py
│   ├── test_sidra_api.py
│   └── test_pipeline_smoke.py
├── data/                        bronze/ e warehouse.duckdb (gitignored)
├── docker-compose.yml
├── Makefile
├── requirements.txt
├── .env.example
└── README.md
```

## 10. Testes

- **Ingestores** — pytest com respostas HTTP simuladas a partir de fixtures
  reais (um CSV INMET reduzido, um JSON SIDRA). Sem rede.
- **Parser do CSV INMET** — casos de vírgula decimal, campo vazio, latin1,
  e as 8 linhas de metadados.
- **Transformações** — testes do dbt (seção 6), mais testes singulares para
  chuva acumulada e cálculo de anomalia.
- **Ponta a ponta** — teste de fumaça com fixtures pequenas e DuckDB
  temporário, verificando que as tabelas Gold ficam populadas.
- **Dashboard** — apenas importação dos módulos e execução das queries. Sem
  teste de interface.

## 11. Riscos

| Risco | Mitigação |
|---|---|
| INMET muda o formato do ZIP ou a URL | Parser isolado em `inmet_api.py`, com teste sobre fixture; falha cedo e com mensagem clara |
| Cobertura desigual de estações por UF | `n_estacoes` exposto no dashboard; média não ponderada documentada como simplificação |
| Lock de escrita no DuckDB durante a janela das 06h | Conexão somente-leitura, curta e com retry no dashboard |
| Carga inicial de ~300 MB é lenta | Ingestão condicional por ano; downloads só uma vez |
| SIDRA muda códigos de classificação | Códigos centralizados em constantes de `sidra_api.py`, não espalhados |

## 12. Execução

**Local, sem Docker:**

```
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python -m src.pipeline
streamlit run dashboard/app.py
```

**Com Docker (inclui Airflow):**

```
cp .env.example .env
docker compose up -d
```

- Dashboard: http://localhost:8501
- Airflow: http://localhost:8080

## 13. Fontes

- [INMET Dados Históricos](https://portal.inmet.gov.br/dadoshistoricos)
- [INMET API de estações](https://apitempo.inmet.gov.br/estacoes/T)
- [IBGE API de agregados (SIDRA)](https://servicodados.ibge.gov.br/api/docs/agregados?versao=3)
