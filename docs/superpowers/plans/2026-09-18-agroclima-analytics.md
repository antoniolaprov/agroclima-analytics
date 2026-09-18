# AgroClima Analytics Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Pipeline que cruza clima do INMET com produção agrícola do IBGE/SIDRA por UF, servido em um dashboard Streamlit.

**Architecture:** Python faz só a ingestão e grava Parquet (Bronze). O dbt-duckdb lê o Parquet e constrói Silver e Gold, e os testes do dbt são o único portão de qualidade. O Airflow agenda, e o Streamlit lê as tabelas Gold do DuckDB.

**Tech Stack:** Python 3.12, pandas, requests, duckdb, dbt-core + dbt-duckdb, Apache Airflow, Streamlit, Plotly, Docker.

**Spec:** `docs/superpowers/specs/2026-09-18-agroclima-analytics-design.md`

## Global Constraints

- Python 3.12 (ambiente verificado: 3.12.10).
- Airflow **não roda nativamente no Windows**. Desenvolvimento local usa
  `python -m src.pipeline` + `streamlit`; o Airflow só sobe via Docker.
- Encoding dos CSVs do INMET: `latin1`. Separador `;`. Decimal com vírgula.
- Valores ausentes do INMET: campo vazio. Tratar também `-9999` e `9999`.
- Anos de clima carregados: 2022 a 2026.
- Culturas: soja, milho, café, cana-de-açúcar.
- Nível geográfico do SIDRA: `N3` (UF).
- Códigos SIDRA PAM (tabela 5457, classificação `c782`): soja `40124`,
  milho `40122`, café total `40139`, cana `40106`.
- Códigos SIDRA LSPA (tabela 6588, classificação `c48`): soja `39443`,
  café total `40527`, cana `39456`, milho 1ª safra `39441`, milho 2ª safra `39442`.
- Variáveis PAM: `8331` área plantada, `216` área colhida, `214` produção,
  `112` rendimento, `215` valor.
- Variáveis LSPA: `109` área plantada, `216` área colhida, `35` produção,
  `36` rendimento.
- **Sem atribuição de IA em nenhum commit, README ou comentário.** Autoria
  exclusiva do usuário.
- **Estilo:** sem emoji; comentário só onde o código não se explica; sem
  banner decorativo; sem try/except defensivo desnecessário; mensagens de
  commit curtas e no imperativo.

---

### Task 1: Esqueleto do projeto e utilitários de ingestão

**Files:**
- Create: `requirements.txt`
- Create: `src/__init__.py`
- Create: `src/config.py`
- Create: `src/ingestion/__init__.py`
- Create: `src/ingestion/base.py`
- Create: `src/ingestion/manifest.py`
- Test: `tests/test_base.py`
- Test: `tests/test_manifest.py`

**Interfaces:**
- Consumes: nada (primeira tarefa)
- Produces:
  - `config.BRONZE_DIR: Path`, `config.DATA_DIR: Path`, `config.DUCKDB_PATH: Path`
  - `config.ANOS_CLIMA: tuple[int, ...]`
  - `config.CULTURAS_PAM: dict[str, str]`, `config.CULTURAS_LSPA: dict[str, str]`
  - `base.http_get(url: str, timeout: int = 60) -> requests.Response`
  - `base.write_parquet(df: pd.DataFrame, nome: str, source_url: str, particao: str | None = None) -> Path`
  - `manifest.ler(chave: str) -> dict | None`
  - `manifest.gravar(chave: str, dados: dict) -> None`

- [ ] **Step 1: Criar requirements.txt**

```
pandas==2.2.3
requests==2.32.3
pyarrow==17.0.0
duckdb==1.1.3
dbt-core==1.8.8
dbt-duckdb==1.8.4
streamlit==1.39.0
plotly==5.24.1
pytest==8.3.3
responses==0.25.3
```

- [ ] **Step 2: Escrever os testes que falham**

```python
# tests/test_manifest.py
from src import manifest_helpers  # noqa  -- placeholder removido no Step 4
```

Use este conteúdo real:

```python
# tests/test_manifest.py
import json
from src.ingestion import manifest


def test_ler_retorna_none_quando_nao_existe(tmp_path, monkeypatch):
    monkeypatch.setattr(manifest, "CAMINHO", tmp_path / "_manifest.json")
    assert manifest.ler("clima_2026") is None


def test_gravar_e_ler_roundtrip(tmp_path, monkeypatch):
    monkeypatch.setattr(manifest, "CAMINHO", tmp_path / "_manifest.json")
    manifest.gravar("clima_2026", {"etag": "abc"})
    assert manifest.ler("clima_2026") == {"etag": "abc"}


def test_gravar_preserva_outras_chaves(tmp_path, monkeypatch):
    monkeypatch.setattr(manifest, "CAMINHO", tmp_path / "_manifest.json")
    manifest.gravar("clima_2025", {"etag": "a"})
    manifest.gravar("clima_2026", {"etag": "b"})
    assert manifest.ler("clima_2025") == {"etag": "a"}
    assert manifest.ler("clima_2026") == {"etag": "b"}
```

```python
# tests/test_base.py
import pandas as pd
from src.ingestion import base


def test_write_parquet_adiciona_colunas_de_controle(tmp_path, monkeypatch):
    monkeypatch.setattr(base.config, "BRONZE_DIR", tmp_path)
    df = pd.DataFrame({"a": [1, 2]})

    caminho = base.write_parquet(df, "teste", "http://exemplo/x")

    lido = pd.read_parquet(caminho)
    assert list(lido["a"]) == [1, 2]
    assert lido["_source_url"].unique().tolist() == ["http://exemplo/x"]
    assert lido["_ingested_at"].notna().all()


def test_write_parquet_com_particao_cria_subpasta(tmp_path, monkeypatch):
    monkeypatch.setattr(base.config, "BRONZE_DIR", tmp_path)
    df = pd.DataFrame({"a": [1]})

    caminho = base.write_parquet(df, "clima", "http://exemplo/x", particao="2026")

    assert caminho.parent.name == "ano=2026"
    assert caminho.parent.parent.name == "clima"
```

- [ ] **Step 3: Rodar os testes e confirmar que falham**

Run: `python -m pytest tests/test_manifest.py tests/test_base.py -v`
Expected: FAIL com `ModuleNotFoundError: No module named 'src'`

- [ ] **Step 4: Implementar config, base e manifest**

```python
# src/config.py
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
DATA_DIR = RAIZ / "data"
BRONZE_DIR = DATA_DIR / "bronze"
DUCKDB_PATH = DATA_DIR / "warehouse.duckdb"

ANOS_CLIMA = (2022, 2023, 2024, 2025, 2026)

INMET_ESTACOES_URL = "https://apitempo.inmet.gov.br/estacoes/T"
INMET_ZIP_URL = "https://portal.inmet.gov.br/uploads/dadoshistoricos/{ano}.zip"

SIDRA_BASE = "https://servicodados.ibge.gov.br/api/v3/agregados"

CULTURAS_PAM = {
    "40124": "soja",
    "40122": "milho",
    "40139": "cafe",
    "40106": "cana",
}

CULTURAS_LSPA = {
    "39443": "soja",
    "39441": "milho",
    "39442": "milho",
    "40527": "cafe",
    "39456": "cana",
}

CICLO_LSPA = {"39441": 1, "39442": 2}
```

```python
# src/ingestion/manifest.py
import json
from pathlib import Path

from src import config

CAMINHO = config.BRONZE_DIR / "_manifest.json"


def _carregar() -> dict:
    if not Path(CAMINHO).exists():
        return {}
    return json.loads(Path(CAMINHO).read_text(encoding="utf-8"))


def ler(chave: str) -> dict | None:
    return _carregar().get(chave)


def gravar(chave: str, dados: dict) -> None:
    tudo = _carregar()
    tudo[chave] = dados
    Path(CAMINHO).parent.mkdir(parents=True, exist_ok=True)
    Path(CAMINHO).write_text(json.dumps(tudo, indent=2), encoding="utf-8")
```

```python
# src/ingestion/base.py
import logging
import time
from pathlib import Path

import pandas as pd
import requests

from src import config

log = logging.getLogger(__name__)


def http_get(url: str, timeout: int = 60, tentativas: int = 3, **kwargs) -> requests.Response:
    for n in range(1, tentativas + 1):
        resposta = requests.get(url, timeout=timeout, **kwargs)
        if resposta.status_code < 500:
            resposta.raise_for_status()
            return resposta
        log.warning("tentativa %s falhou para %s (%s)", n, url, resposta.status_code)
        time.sleep(2 ** n)
    resposta.raise_for_status()
    return resposta


def write_parquet(df: pd.DataFrame, nome: str, source_url: str, particao: str | None = None) -> Path:
    df = df.copy()
    df["_ingested_at"] = pd.Timestamp.utcnow()
    df["_source_url"] = source_url

    destino = Path(config.BRONZE_DIR) / nome
    if particao is not None:
        destino = destino / f"ano={particao}"
    destino.mkdir(parents=True, exist_ok=True)

    caminho = destino / "dados.parquet"
    df.to_parquet(caminho, index=False)
    log.info("gravado %s (%s linhas)", caminho, len(df))
    return caminho
```

Criar `src/__init__.py` e `src/ingestion/__init__.py` vazios.

- [ ] **Step 5: Rodar os testes e confirmar que passam**

Run: `python -m pytest tests/test_manifest.py tests/test_base.py -v`
Expected: PASS (5 testes)

- [ ] **Step 6: Commit**

```bash
git add requirements.txt src tests
git commit -m "Add project scaffolding and ingestion helpers"
```

---

### Task 2: Ingestão do catálogo de estações do INMET

**Files:**
- Create: `src/ingestion/inmet_api.py`
- Test: `tests/test_inmet_estacoes.py`
- Test: `tests/fixtures/estacoes.json`

**Interfaces:**
- Consumes: `base.http_get`, `base.write_parquet`, `config.INMET_ESTACOES_URL`
- Produces: `inmet_api.fetch_estacoes() -> pd.DataFrame`,
  `inmet_api.ingest_estacoes() -> int` (retorna número de linhas gravadas)

- [ ] **Step 1: Criar a fixture**

```json
[
  {
    "CD_ESTACAO": "A001",
    "DC_NOME": "BRASILIA",
    "SG_ESTADO": "DF",
    "VL_LATITUDE": "-15.78944444",
    "VL_LONGITUDE": "-47.92583332",
    "VL_ALTITUDE": "1160.96",
    "CD_SITUACAO": "Operante",
    "DT_INICIO_OPERACAO": "2000-05-07T00:00:00.000-03:00",
    "DT_FIM_OPERACAO": null
  },
  {
    "CD_ESTACAO": "A999",
    "DC_NOME": "DESATIVADA",
    "SG_ESTADO": "BA",
    "VL_LATITUDE": "-11.65",
    "VL_LONGITUDE": "-38.01",
    "VL_ALTITUDE": "182",
    "CD_SITUACAO": "Pane",
    "DT_INICIO_OPERACAO": "2010-01-01T00:00:00.000-03:00",
    "DT_FIM_OPERACAO": "2020-01-01T00:00:00.000-03:00"
  }
]
```

- [ ] **Step 2: Escrever o teste que falha**

```python
# tests/test_inmet_estacoes.py
import json
from pathlib import Path

import responses

from src import config
from src.ingestion import inmet_api

FIXTURE = Path(__file__).parent / "fixtures" / "estacoes.json"


@responses.activate
def test_fetch_estacoes_tipa_colunas_numericas():
    responses.add(
        responses.GET,
        config.INMET_ESTACOES_URL,
        json=json.loads(FIXTURE.read_text(encoding="utf-8")),
        status=200,
    )

    df = inmet_api.fetch_estacoes()

    assert len(df) == 2
    assert df["latitude"].dtype.kind == "f"
    assert df.loc[df["cd_estacao"] == "A001", "latitude"].item() == -15.78944444
    assert set(df.columns) >= {"cd_estacao", "uf", "nome", "latitude", "longitude", "altitude", "situacao"}


@responses.activate
def test_fetch_estacoes_preserva_estacoes_nao_operantes():
    responses.add(
        responses.GET,
        config.INMET_ESTACOES_URL,
        json=json.loads(FIXTURE.read_text(encoding="utf-8")),
        status=200,
    )

    df = inmet_api.fetch_estacoes()

    assert set(df["situacao"]) == {"Operante", "Pane"}
```

O filtro de operantes é responsabilidade do dbt (`stg_estacoes`), não da
ingestão: Bronze guarda o que a fonte deu.

- [ ] **Step 3: Rodar e confirmar que falha**

Run: `python -m pytest tests/test_inmet_estacoes.py -v`
Expected: FAIL com `ImportError: cannot import name 'inmet_api'`

- [ ] **Step 4: Implementar**

```python
# src/ingestion/inmet_api.py
import logging

import pandas as pd

from src import config
from src.ingestion import base

log = logging.getLogger(__name__)

COLUNAS_ESTACAO = {
    "CD_ESTACAO": "cd_estacao",
    "DC_NOME": "nome",
    "SG_ESTADO": "uf",
    "VL_LATITUDE": "latitude",
    "VL_LONGITUDE": "longitude",
    "VL_ALTITUDE": "altitude",
    "CD_SITUACAO": "situacao",
    "DT_INICIO_OPERACAO": "inicio_operacao",
    "DT_FIM_OPERACAO": "fim_operacao",
}


def fetch_estacoes() -> pd.DataFrame:
    resposta = base.http_get(config.INMET_ESTACOES_URL)
    df = pd.DataFrame(resposta.json())

    faltando = set(COLUNAS_ESTACAO) - set(df.columns)
    if faltando:
        raise ValueError(f"resposta do INMET sem as colunas {sorted(faltando)}")

    df = df[list(COLUNAS_ESTACAO)].rename(columns=COLUNAS_ESTACAO)
    for coluna in ("latitude", "longitude", "altitude"):
        df[coluna] = pd.to_numeric(df[coluna], errors="coerce")
    return df


def ingest_estacoes() -> int:
    df = fetch_estacoes()
    base.write_parquet(df, "estacoes", config.INMET_ESTACOES_URL)
    return len(df)
```

- [ ] **Step 5: Rodar e confirmar que passa**

Run: `python -m pytest tests/test_inmet_estacoes.py -v`
Expected: PASS (2 testes)

- [ ] **Step 6: Commit**

```bash
git add src/ingestion/inmet_api.py tests/test_inmet_estacoes.py tests/fixtures/estacoes.json
git commit -m "Add INMET station catalog ingestion"
```

---

### Task 3: Parser do CSV horário do INMET

Esta é a parte mais delicada do projeto: 8 linhas de metadados, latin1,
vírgula decimal e campo vazio como ausente.

**Files:**
- Modify: `src/ingestion/inmet_api.py`
- Test: `tests/test_inmet_csv.py`
- Test: `tests/fixtures/INMET_CO_DF_A001_BRASILIA_01-01-2026_A_31-08-2026.CSV`

**Interfaces:**
- Consumes: nada novo
- Produces: `inmet_api.parse_csv_estacao(conteudo: bytes, nome_arquivo: str) -> pd.DataFrame`
  com colunas `cd_estacao`, `uf`, `data`, `hora_utc`, `precipitacao`,
  `temperatura`, `temperatura_max`, `temperatura_min`, `umidade`,
  `vento_velocidade`

- [ ] **Step 1: Criar a fixture (encoding latin1)**

Gerar com este script, para garantir o encoding correto:

```python
conteudo = """REGIAO:;CO
UF:;DF
ESTACAO:;BRASILIA
CODIGO (WMO):;A001
LATITUDE:;-15,78944444
LONGITUDE:;-47,92583332
ALTITUDE:;1160,96
DATA DE FUNDACAO:;07/05/00
Data;Hora UTC;PRECIPITAÇÃO TOTAL, HORÁRIO (mm);PRESSAO ATMOSFERICA AO NIVEL DA ESTACAO, HORARIA (mB);PRESSÃO ATMOSFERICA MAX.NA HORA ANT. (AUT) (mB);PRESSÃO ATMOSFERICA MIN. NA HORA ANT. (AUT) (mB);RADIACAO GLOBAL (Kj/m²);TEMPERATURA DO AR - BULBO SECO, HORARIA (°C);TEMPERATURA DO PONTO DE ORVALHO (°C);TEMPERATURA MÁXIMA NA HORA ANT. (AUT) (°C);TEMPERATURA MÍNIMA NA HORA ANT. (AUT) (°C);TEMPERATURA ORVALHO MAX. NA HORA ANT. (AUT) (°C);TEMPERATURA ORVALHO MIN. NA HORA ANT. (AUT) (°C);UMIDADE REL. MAX. NA HORA ANT. (AUT) (%);UMIDADE REL. MIN. NA HORA ANT. (AUT) (%);UMIDADE RELATIVA DO AR, HORARIA (%);VENTO, DIREÇÃO HORARIA (gr) (° (gr));VENTO, RAJADA MAXIMA (m/s);VENTO, VELOCIDADE HORARIA (m/s);
2026/01/01;0000 UTC;0;887,7;887,7;887,2;;19,9;18,5;20,8;19,8;18,6;18,1;92;85;92;9;4,5;1,1;
2026/01/01;0100 UTC;0,2;888,1;888,2;887,7;;18,5;17,7;19,8;18,5;18,4;17,7;95;92;95;305;1,8;,8;
2026/01/01;0200 UTC;;888;888,2;888;;-9999;17,5;18,5;18,1;17,8;17,4;96;95;96;301;1,9;1;
"""
caminho = "tests/fixtures/INMET_CO_DF_A001_BRASILIA_01-01-2026_A_31-08-2026.CSV"
open(caminho, "w", encoding="latin1", newline="").write(conteudo)
```

A fixture cobre os três casos que importam: valor normal, decimal iniciado
por vírgula (`,8`), campo vazio e sentinela `-9999`.

- [ ] **Step 2: Escrever o teste que falha**

```python
# tests/test_inmet_csv.py
import math
from pathlib import Path

import pandas as pd

from src.ingestion import inmet_api

FIXTURE = Path(__file__).parent / "fixtures" / "INMET_CO_DF_A001_BRASILIA_01-01-2026_A_31-08-2026.CSV"


def _parse():
    return inmet_api.parse_csv_estacao(FIXTURE.read_bytes(), FIXTURE.name)


def test_pula_metadados_e_le_tres_linhas():
    assert len(_parse()) == 3


def test_extrai_estacao_e_uf_do_nome_do_arquivo():
    df = _parse()
    assert set(df["cd_estacao"]) == {"A001"}
    assert set(df["uf"]) == {"DF"}


def test_converte_virgula_decimal():
    df = _parse()
    assert df.loc[0, "temperatura"] == 19.9
    assert df.loc[1, "precipitacao"] == 0.2


def test_decimal_iniciado_por_virgula():
    df = _parse()
    assert df.loc[1, "vento_velocidade"] == 0.8


def test_campo_vazio_vira_nulo():
    df = _parse()
    assert math.isnan(df.loc[2, "precipitacao"])


def test_sentinela_menos_9999_vira_nulo():
    df = _parse()
    assert math.isnan(df.loc[2, "temperatura"])


def test_hora_utc_vira_inteiro():
    df = _parse()
    assert list(df["hora_utc"]) == [0, 1, 2]


def test_data_vira_datetime():
    df = _parse()
    assert df["data"].dtype.kind == "M"
    assert df.loc[0, "data"] == pd.Timestamp("2026-01-01")
```

- [ ] **Step 3: Rodar e confirmar que falha**

Run: `python -m pytest tests/test_inmet_csv.py -v`
Expected: FAIL com `AttributeError: module 'src.ingestion.inmet_api' has no attribute 'parse_csv_estacao'`

- [ ] **Step 4: Implementar**

Acrescentar a `src/ingestion/inmet_api.py`:

```python
import io
import re

SENTINELAS = {"", "-9999", "9999", "null"}

COLUNAS_CSV = {
    "PRECIPITAÇÃO TOTAL, HORÁRIO (mm)": "precipitacao",
    "TEMPERATURA DO AR - BULBO SECO, HORARIA (°C)": "temperatura",
    "TEMPERATURA MÁXIMA NA HORA ANT. (AUT) (°C)": "temperatura_max",
    "TEMPERATURA MÍNIMA NA HORA ANT. (AUT) (°C)": "temperatura_min",
    "UMIDADE RELATIVA DO AR, HORARIA (%)": "umidade",
    "VENTO, VELOCIDADE HORARIA (m/s)": "vento_velocidade",
}

PADRAO_NOME = re.compile(r"INMET_[A-Z]{1,2}_([A-Z]{2})_([A-Z]\d{3})_")


def _para_float(valor: str) -> float:
    texto = str(valor).strip()
    if texto in SENTINELAS:
        return float("nan")
    return float(texto.replace(",", "."))


def parse_csv_estacao(conteudo: bytes, nome_arquivo: str) -> pd.DataFrame:
    achado = PADRAO_NOME.search(nome_arquivo)
    if achado is None:
        raise ValueError(f"nome de arquivo fora do padrao do INMET: {nome_arquivo}")
    uf, cd_estacao = achado.groups()

    texto = conteudo.decode("latin1")
    df = pd.read_csv(io.StringIO(texto), sep=";", skiprows=8, dtype=str)
    df.columns = [c.strip() for c in df.columns]

    presentes = {orig: novo for orig, novo in COLUNAS_CSV.items() if orig in df.columns}
    if len(presentes) != len(COLUNAS_CSV):
        faltando = sorted(set(COLUNAS_CSV) - set(presentes))
        raise ValueError(f"CSV {nome_arquivo} sem as colunas {faltando}")

    saida = pd.DataFrame(
        {
            "cd_estacao": cd_estacao,
            "uf": uf,
            "data": pd.to_datetime(df["Data"], format="%Y/%m/%d"),
            "hora_utc": df["Hora UTC"].str.slice(0, 2).astype(int),
        }
    )
    for original, novo in presentes.items():
        saida[novo] = df[original].map(_para_float)
    return saida
```

- [ ] **Step 5: Rodar e confirmar que passa**

Run: `python -m pytest tests/test_inmet_csv.py -v`
Expected: PASS (8 testes)

- [ ] **Step 6: Commit**

```bash
git add src/ingestion/inmet_api.py tests/test_inmet_csv.py tests/fixtures/
git commit -m "Parse INMET hourly CSV with latin1 and comma decimals"
```

---

### Task 4: Download condicional do ZIP anual

**Files:**
- Modify: `src/ingestion/inmet_api.py`
- Test: `tests/test_inmet_zip.py`

**Interfaces:**
- Consumes: `manifest.ler`, `manifest.gravar`, `inmet_api.parse_csv_estacao`
- Produces:
  - `inmet_api.zip_mudou(ano: int) -> tuple[bool, dict]` — retorna se mudou e os headers novos
  - `inmet_api.ingest_clima(anos: Iterable[int]) -> dict[int, int]` — ano para linhas gravadas; ano sem mudança recebe `0`

- [ ] **Step 1: Escrever os testes que falham**

```python
# tests/test_inmet_zip.py
import io
import zipfile

import responses

from src import config
from src.ingestion import inmet_api, manifest


def _url(ano):
    return config.INMET_ZIP_URL.format(ano=ano)


def _zip_de_uma_estacao():
    conteudo = (
        "REGIAO:;CO\nUF:;DF\nESTACAO:;BRASILIA\nCODIGO (WMO):;A001\n"
        "LATITUDE:;-15,7\nLONGITUDE:;-47,9\nALTITUDE:;1160\nDATA DE FUNDACAO:;07/05/00\n"
        "Data;Hora UTC;PRECIPITAÇÃO TOTAL, HORÁRIO (mm);"
        "TEMPERATURA DO AR - BULBO SECO, HORARIA (°C);"
        "TEMPERATURA MÁXIMA NA HORA ANT. (AUT) (°C);"
        "TEMPERATURA MÍNIMA NA HORA ANT. (AUT) (°C);"
        "UMIDADE RELATIVA DO AR, HORARIA (%);"
        "VENTO, VELOCIDADE HORARIA (m/s);\n"
        "2026/01/01;0000 UTC;0;19,9;20,8;19,8;92;1,1;\n"
    )
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as z:
        z.writestr(
            "INMET_CO_DF_A001_BRASILIA_01-01-2026_A_31-08-2026.CSV",
            conteudo.encode("latin1"),
        )
    return buffer.getvalue()


@responses.activate
def test_zip_mudou_quando_nao_ha_manifest(tmp_path, monkeypatch):
    monkeypatch.setattr(manifest, "CAMINHO", tmp_path / "_manifest.json")
    responses.add(responses.HEAD, _url(2026), headers={"ETag": "v1"}, status=200)

    mudou, headers = inmet_api.zip_mudou(2026)

    assert mudou is True
    assert headers["etag"] == "v1"


@responses.activate
def test_zip_nao_mudou_quando_etag_igual(tmp_path, monkeypatch):
    monkeypatch.setattr(manifest, "CAMINHO", tmp_path / "_manifest.json")
    manifest.gravar("clima_2026", {"etag": "v1", "last_modified": None})
    responses.add(responses.HEAD, _url(2026), headers={"ETag": "v1"}, status=200)

    mudou, _ = inmet_api.zip_mudou(2026)

    assert mudou is False


@responses.activate
def test_ingest_clima_pula_ano_sem_mudanca(tmp_path, monkeypatch):
    monkeypatch.setattr(manifest, "CAMINHO", tmp_path / "_manifest.json")
    monkeypatch.setattr(config, "BRONZE_DIR", tmp_path)
    manifest.gravar("clima_2026", {"etag": "v1", "last_modified": None})
    responses.add(responses.HEAD, _url(2026), headers={"ETag": "v1"}, status=200)

    assert inmet_api.ingest_clima([2026]) == {2026: 0}


@responses.activate
def test_ingest_clima_baixa_e_grava_quando_mudou(tmp_path, monkeypatch):
    monkeypatch.setattr(manifest, "CAMINHO", tmp_path / "_manifest.json")
    monkeypatch.setattr(config, "BRONZE_DIR", tmp_path)
    responses.add(responses.HEAD, _url(2026), headers={"ETag": "v2"}, status=200)
    responses.add(responses.GET, _url(2026), body=_zip_de_uma_estacao(), status=200)

    resultado = inmet_api.ingest_clima([2026])

    assert resultado == {2026: 1}
    assert (tmp_path / "clima_horario" / "ano=2026" / "dados.parquet").exists()
    assert manifest.ler("clima_2026")["etag"] == "v2"
```

- [ ] **Step 2: Rodar e confirmar que falha**

Run: `python -m pytest tests/test_inmet_zip.py -v`
Expected: FAIL com `AttributeError: ... has no attribute 'zip_mudou'`

- [ ] **Step 3: Implementar**

Acrescentar a `src/ingestion/inmet_api.py`:

```python
import zipfile
from typing import Iterable

import requests

from src.ingestion import manifest


def zip_mudou(ano: int) -> tuple[bool, dict]:
    url = config.INMET_ZIP_URL.format(ano=ano)
    cabecalho = requests.head(url, timeout=60, allow_redirects=True)
    cabecalho.raise_for_status()

    atual = {
        "etag": cabecalho.headers.get("ETag"),
        "last_modified": cabecalho.headers.get("Last-Modified"),
    }
    anterior = manifest.ler(f"clima_{ano}")
    if anterior is None:
        return True, atual
    if atual["etag"] and atual["etag"] == anterior.get("etag"):
        return False, atual
    if atual["last_modified"] and atual["last_modified"] == anterior.get("last_modified"):
        return False, atual
    return True, atual


def _ler_zip(conteudo: bytes) -> pd.DataFrame:
    partes = []
    with zipfile.ZipFile(io.BytesIO(conteudo)) as z:
        for nome in z.namelist():
            if not nome.upper().endswith(".CSV"):
                continue
            try:
                partes.append(parse_csv_estacao(z.read(nome), nome.split("/")[-1]))
            except ValueError as erro:
                log.warning("ignorando %s: %s", nome, erro)
    if not partes:
        raise ValueError("nenhum CSV valido no zip")
    return pd.concat(partes, ignore_index=True)


def ingest_clima(anos: Iterable[int]) -> dict[int, int]:
    resultado = {}
    for ano in anos:
        mudou, headers = zip_mudou(ano)
        if not mudou:
            log.info("clima %s sem mudanca, pulando", ano)
            resultado[ano] = 0
            continue

        url = config.INMET_ZIP_URL.format(ano=ano)
        df = _ler_zip(base.http_get(url, timeout=600).content)
        base.write_parquet(df, "clima_horario", url, particao=str(ano))
        manifest.gravar(f"clima_{ano}", headers)
        resultado[ano] = len(df)
    return resultado
```

O `except ValueError` aqui não é defensivo genérico: o ZIP real tem
arquivos cujo nome foge do padrão, e ignorar um CSV isolado é melhor que
perder o ano inteiro.

- [ ] **Step 4: Rodar e confirmar que passa**

Run: `python -m pytest tests/test_inmet_zip.py -v`
Expected: PASS (4 testes)

- [ ] **Step 5: Commit**

```bash
git add src/ingestion/inmet_api.py tests/test_inmet_zip.py
git commit -m "Download INMET yearly archive only when it changed"
```

---

### Task 5: Ingestão do SIDRA (PAM e LSPA)

**Files:**
- Create: `src/ingestion/sidra_api.py`
- Test: `tests/test_sidra.py`
- Test: `tests/fixtures/sidra_pam.json`

**Interfaces:**
- Consumes: `base.http_get`, `base.write_parquet`, `config.SIDRA_BASE`,
  `config.CULTURAS_PAM`, `config.CULTURAS_LSPA`, `config.CICLO_LSPA`
- Produces:
  - `sidra_api.parse_resposta(payload: list, mapa_culturas: dict) -> pd.DataFrame`
    com colunas `uf_codigo`, `uf_nome`, `cultura`, `periodo`, `variavel`, `valor`
  - `sidra_api.ingest_pam() -> int`
  - `sidra_api.ingest_lspa() -> int`

- [ ] **Step 1: Criar a fixture**

```json
[
  {
    "id": "214",
    "variavel": "Quantidade produzida",
    "unidade": "Toneladas",
    "resultados": [
      {
        "classificacoes": [
          {"id": "782", "nome": "Produto", "categoria": {"40124": "Soja (em grao)"}}
        ],
        "series": [
          {"localidade": {"id": "41", "nome": "Parana"}, "serie": {"2024": "18689393"}},
          {"localidade": {"id": "51", "nome": "Mato Grosso"}, "serie": {"2024": "38396410"}}
        ]
      }
    ]
  },
  {
    "id": "112",
    "variavel": "Rendimento medio da producao",
    "unidade": "Quilogramas por Hectare",
    "resultados": [
      {
        "classificacoes": [
          {"id": "782", "nome": "Produto", "categoria": {"40124": "Soja (em grao)"}}
        ],
        "series": [
          {"localidade": {"id": "41", "nome": "Parana"}, "serie": {"2024": "3240"}},
          {"localidade": {"id": "51", "nome": "Mato Grosso"}, "serie": {"2024": "..."}}
        ]
      }
    ]
  }
]
```

O valor `"..."` é como o SIDRA representa dado ausente.

- [ ] **Step 2: Escrever o teste que falha**

```python
# tests/test_sidra.py
import json
import math
from pathlib import Path

from src.ingestion import sidra_api

FIXTURE = Path(__file__).parent / "fixtures" / "sidra_pam.json"
MAPA = {"40124": "soja"}


def _parse():
    return sidra_api.parse_resposta(json.loads(FIXTURE.read_text(encoding="utf-8")), MAPA)


def test_achata_para_linhas_longas():
    df = _parse()
    assert len(df) == 4
    assert set(df["variavel"]) == {"214", "112"}


def test_mapeia_cultura_pelo_codigo():
    assert set(_parse()["cultura"]) == {"soja"}


def test_converte_valor_para_float():
    df = _parse()
    linha = df[(df["uf_codigo"] == "41") & (df["variavel"] == "214")]
    assert linha["valor"].item() == 18689393.0


def test_reticencias_vira_nulo():
    df = _parse()
    linha = df[(df["uf_codigo"] == "51") & (df["variavel"] == "112")]
    assert math.isnan(linha["valor"].item())


def test_periodo_preservado():
    assert set(_parse()["periodo"]) == {"2024"}
```

- [ ] **Step 3: Rodar e confirmar que falha**

Run: `python -m pytest tests/test_sidra.py -v`
Expected: FAIL com `ModuleNotFoundError: No module named 'src.ingestion.sidra_api'`

- [ ] **Step 4: Implementar**

```python
# src/ingestion/sidra_api.py
import logging

import pandas as pd

from src import config
from src.ingestion import base

log = logging.getLogger(__name__)

AUSENTES = {"...", "-", "..", "X"}

VARIAVEIS_PAM = ["8331", "216", "214", "112", "215"]
VARIAVEIS_LSPA = ["109", "216", "35", "36"]


def _para_float(valor: str) -> float:
    if valor is None or str(valor).strip() in AUSENTES:
        return float("nan")
    return float(valor)


def montar_url(tabela: str, periodos: str, variaveis: list[str], classificacao: str, categorias: list[str]) -> str:
    return (
        f"{config.SIDRA_BASE}/{tabela}/periodos/{periodos}"
        f"/variaveis/{'|'.join(variaveis)}"
        f"?localidades=N3[all]&classificacao={classificacao}[{','.join(categorias)}]"
    )


def parse_resposta(payload: list, mapa_culturas: dict) -> pd.DataFrame:
    linhas = []
    for bloco in payload:
        variavel = bloco["id"]
        for resultado in bloco["resultados"]:
            categoria = resultado["classificacoes"][0]["categoria"]
            codigo = next(iter(categoria))
            cultura = mapa_culturas.get(codigo)
            if cultura is None:
                continue
            for serie in resultado["series"]:
                for periodo, valor in serie["serie"].items():
                    linhas.append(
                        {
                            "uf_codigo": serie["localidade"]["id"],
                            "uf_nome": serie["localidade"]["nome"],
                            "cultura": cultura,
                            "cultura_codigo": codigo,
                            "periodo": periodo,
                            "variavel": variavel,
                            "valor": _para_float(valor),
                        }
                    )
    return pd.DataFrame(linhas)


def ingest_pam() -> int:
    url = montar_url("5457", "all", VARIAVEIS_PAM, "782", list(config.CULTURAS_PAM))
    df = parse_resposta(base.http_get(url, timeout=180).json(), config.CULTURAS_PAM)
    base.write_parquet(df, "pam", url)
    return len(df)


def ingest_lspa() -> int:
    url = montar_url("6588", "all", VARIAVEIS_LSPA, "48", list(config.CULTURAS_LSPA))
    df = parse_resposta(base.http_get(url, timeout=180).json(), config.CULTURAS_LSPA)
    df["safra_ciclo"] = df["cultura_codigo"].map(config.CICLO_LSPA)
    base.write_parquet(df, "lspa", url)
    return len(df)
```

- [ ] **Step 5: Rodar e confirmar que passa**

Run: `python -m pytest tests/test_sidra.py -v`
Expected: PASS (5 testes)

- [ ] **Step 6: Commit**

```bash
git add src/ingestion/sidra_api.py tests/test_sidra.py tests/fixtures/sidra_pam.json
git commit -m "Add SIDRA ingestion for PAM and LSPA tables"
```

---

### Task 6: Orquestração do pipeline

**Files:**
- Create: `src/pipeline.py`
- Test: `tests/test_pipeline.py`

**Interfaces:**
- Consumes: `inmet_api.ingest_estacoes`, `inmet_api.ingest_clima`,
  `sidra_api.ingest_pam`, `sidra_api.ingest_lspa`
- Produces: `pipeline.ingerir(anos=None) -> dict`, `pipeline.rodar_dbt() -> None`,
  `pipeline.main(anos=None) -> dict`

- [ ] **Step 1: Escrever o teste que falha**

```python
# tests/test_pipeline.py
import pytest

from src import config, pipeline


def test_ingerir_chama_todas_as_fontes(monkeypatch):
    chamadas = []
    monkeypatch.setattr(pipeline.inmet_api, "ingest_estacoes", lambda: chamadas.append("estacoes") or 674)
    monkeypatch.setattr(pipeline.inmet_api, "ingest_clima", lambda anos: chamadas.append("clima") or {2026: 10})
    monkeypatch.setattr(pipeline.sidra_api, "ingest_pam", lambda: chamadas.append("pam") or 100)
    monkeypatch.setattr(pipeline.sidra_api, "ingest_lspa", lambda: chamadas.append("lspa") or 50)

    resumo = pipeline.ingerir([2026])

    assert chamadas == ["estacoes", "clima", "pam", "lspa"]
    assert resumo == {"estacoes": 674, "clima": {2026: 10}, "pam": 100, "lspa": 50}


def test_ingerir_usa_anos_do_config_por_padrao(monkeypatch):
    recebido = {}
    monkeypatch.setattr(pipeline.inmet_api, "ingest_estacoes", lambda: 0)
    monkeypatch.setattr(pipeline.inmet_api, "ingest_clima", lambda anos: recebido.setdefault("anos", list(anos)) or {})
    monkeypatch.setattr(pipeline.sidra_api, "ingest_pam", lambda: 0)
    monkeypatch.setattr(pipeline.sidra_api, "ingest_lspa", lambda: 0)

    pipeline.ingerir()

    assert recebido["anos"] == list(config.ANOS_CLIMA)


def test_rodar_dbt_propaga_falha(monkeypatch):
    def falso_run(*args, **kwargs):
        class R:
            returncode = 1
        return R()

    monkeypatch.setattr(pipeline.subprocess, "run", falso_run)

    with pytest.raises(RuntimeError, match="dbt build falhou"):
        pipeline.rodar_dbt()
```

- [ ] **Step 2: Rodar e confirmar que falha**

Run: `python -m pytest tests/test_pipeline.py -v`
Expected: FAIL com `ModuleNotFoundError: No module named 'src.pipeline'`

- [ ] **Step 3: Implementar**

```python
# src/pipeline.py
import logging
import subprocess

from src import config
from src.ingestion import inmet_api, sidra_api

log = logging.getLogger(__name__)

DBT_DIR = config.RAIZ / "dbt"


def ingerir(anos=None) -> dict:
    anos = list(config.ANOS_CLIMA) if anos is None else list(anos)
    return {
        "estacoes": inmet_api.ingest_estacoes(),
        "clima": inmet_api.ingest_clima(anos),
        "pam": sidra_api.ingest_pam(),
        "lspa": sidra_api.ingest_lspa(),
    }


def rodar_dbt() -> None:
    resultado = subprocess.run(
        ["dbt", "build", "--project-dir", str(DBT_DIR), "--profiles-dir", str(DBT_DIR)],
        check=False,
    )
    if resultado.returncode != 0:
        raise RuntimeError("dbt build falhou")


def main(anos=None) -> dict:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    resumo = ingerir(anos)
    rodar_dbt()
    log.info("pipeline concluido: %s", resumo)
    return resumo


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Rodar e confirmar que passa**

Run: `python -m pytest tests/test_pipeline.py -v`
Expected: PASS (3 testes)

- [ ] **Step 5: Commit**

```bash
git add src/pipeline.py tests/test_pipeline.py
git commit -m "Wire ingestion and dbt build into a single entry point"
```

---

### Task 7: Projeto dbt e camada Silver

**Files:**
- Create: `dbt/dbt_project.yml`, `dbt/profiles.yml`
- Create: `dbt/models/staging/sources.yml`, `dbt/models/staging/schema.yml`
- Create: `dbt/models/staging/stg_estacoes.sql`, `stg_clima_horario.sql`,
  `stg_clima_diario.sql`, `stg_pam.sql`, `stg_lspa.sql`

**Interfaces:**
- Consumes: Parquet em `data/bronze/` das Tasks 2 a 5
- Produces:
  - `stg_estacoes(cd_estacao, uf, nome, latitude, longitude, altitude)`
  - `stg_clima_diario(cd_estacao, uf, data, temp_media, temp_max, temp_min, precipitacao, umidade_media, horas_observadas)`
  - `stg_pam(uf_codigo, uf_nome, cultura, ano, area_plantada, area_colhida, producao, rendimento)`
  - `stg_lspa(uf_codigo, cultura, safra_ciclo, ano, mes, area_plantada, producao, rendimento)`

- [ ] **Step 1: Criar a configuração do dbt**

```yaml
# dbt/dbt_project.yml
name: agroclima
version: "1.0"
profile: agroclima

model-paths: ["models"]
seed-paths: ["seeds"]
test-paths: ["tests"]
target-path: "target"

models:
  agroclima:
    staging:
      +materialized: view
      stg_clima_horario:
        +materialized: table
      stg_clima_diario:
        +materialized: table
    marts:
      +materialized: table
```

```yaml
# dbt/profiles.yml
agroclima:
  target: dev
  outputs:
    dev:
      type: duckdb
      path: "../data/warehouse.duckdb"
      threads: 4
```

```yaml
# dbt/models/staging/sources.yml
version: 2

sources:
  - name: bronze
    meta:
      external_location: "../data/bronze/{name}/**/*.parquet"
    tables:
      - name: estacoes
      - name: clima_horario
      - name: pam
      - name: lspa
```

- [ ] **Step 2: Escrever os testes dbt que falham**

```yaml
# dbt/models/staging/schema.yml
version: 2

models:
  - name: stg_estacoes
    columns:
      - name: cd_estacao
        tests: [not_null, unique]
      - name: uf
        tests:
          - not_null
          - accepted_values:
              values: ['AC','AL','AP','AM','BA','CE','DF','ES','GO','MA','MT','MS','MG','PA','PB','PR','PE','PI','RJ','RN','RS','RO','RR','SC','SP','SE','TO']

  - name: stg_clima_diario
    columns:
      - name: uf
        tests: [not_null]
      - name: data
        tests: [not_null]
      - name: temp_media
        tests:
          - dbt_utils.accepted_range:
              min_value: -10
              max_value: 50
              severity: warn
      - name: precipitacao
        tests:
          - dbt_utils.accepted_range:
              min_value: 0
    tests:
      - dbt_utils.unique_combination_of_columns:
          combination_of_columns: [cd_estacao, data]

  - name: stg_pam
    columns:
      - name: cultura
        tests:
          - not_null
          - accepted_values:
              values: ['soja', 'milho', 'cafe', 'cana']
```

Adicionar `dbt/packages.yml`:

```yaml
packages:
  - package: dbt-labs/dbt_utils
    version: 1.3.0
```

- [ ] **Step 3: Rodar e confirmar que falha**

Run: `cd dbt && dbt deps && dbt build --select staging`
Expected: FAIL — modelos `stg_*` não existem

- [ ] **Step 4: Implementar os modelos**

```sql
-- dbt/models/staging/stg_estacoes.sql
select
    cd_estacao,
    upper(trim(uf))    as uf,
    nome,
    latitude,
    longitude,
    altitude
from {{ source('bronze', 'estacoes') }}
where situacao = 'Operante'
  and fim_operacao is null
```

```sql
-- dbt/models/staging/stg_clima_horario.sql
select
    cd_estacao,
    upper(trim(uf)) as uf,
    cast(data as date) as data,
    hora_utc,
    precipitacao,
    temperatura,
    temperatura_max,
    temperatura_min,
    umidade,
    vento_velocidade
from {{ source('bronze', 'clima_horario') }}
```

```sql
-- dbt/models/staging/stg_clima_diario.sql
with por_dia as (
    select
        h.cd_estacao,
        e.uf,
        h.data,
        avg(h.temperatura)      as temp_media,
        max(h.temperatura_max)  as temp_max,
        min(h.temperatura_min)  as temp_min,
        sum(h.precipitacao)     as precipitacao,
        avg(h.umidade)          as umidade_media,
        count(h.temperatura)    as horas_observadas
    from {{ ref('stg_clima_horario') }} h
    inner join {{ ref('stg_estacoes') }} e on e.cd_estacao = h.cd_estacao
    group by 1, 2, 3
)
select *
from por_dia
where horas_observadas >= 18
```

```sql
-- dbt/models/staging/stg_pam.sql
select
    uf_codigo,
    uf_nome,
    cultura,
    cast(periodo as integer) as ano,
    max(case when variavel = '8331' then valor end) as area_plantada,
    max(case when variavel = '216'  then valor end) as area_colhida,
    max(case when variavel = '214'  then valor end) as producao,
    max(case when variavel = '112'  then valor end) as rendimento
from {{ source('bronze', 'pam') }}
group by 1, 2, 3, 4
```

```sql
-- dbt/models/staging/stg_lspa.sql
select
    uf_codigo,
    uf_nome,
    cultura,
    safra_ciclo,
    cast(substr(periodo, 1, 4) as integer) as ano,
    cast(substr(periodo, 5, 2) as integer) as mes,
    max(case when variavel = '109' then valor end) as area_plantada,
    max(case when variavel = '35'  then valor end) as producao,
    max(case when variavel = '36'  then valor end) as rendimento
from {{ source('bronze', 'lspa') }}
group by 1, 2, 3, 4, 5, 6
```

- [ ] **Step 5: Rodar e confirmar que passa**

Run: `cd dbt && dbt build --select staging`
Expected: PASS — modelos criados e testes verdes

- [ ] **Step 6: Commit**

```bash
git add dbt/
git commit -m "Add dbt project and staging models"
```

---

### Task 8: Dimensões e seed do ciclo das culturas

**Files:**
- Create: `dbt/seeds/ciclo_cultura.csv`, `dbt/seeds/schema.yml`
- Create: `dbt/models/staging/dim_uf.sql`, `dbt/models/staging/dim_cultura.sql`
- Modify: `dbt/models/staging/schema.yml`

**Interfaces:**
- Consumes: `stg_estacoes`, `stg_pam`
- Produces:
  - `dim_uf(uf, uf_codigo, uf_nome, regiao)`
  - `dim_cultura(cultura, nome_exibicao)`
  - seed `ciclo_cultura(cultura, mes_inicio, mes_fim)`

- [ ] **Step 1: Criar o seed**

```csv
cultura,mes_inicio,mes_fim
soja,10,3
milho,9,7
cafe,9,8
cana,4,11
```

`mes_inicio > mes_fim` significa ciclo que cruza o ano (soja planta em
outubro e colhe em março do ano seguinte). A Task 9 trata isso.

```yaml
# dbt/seeds/schema.yml
version: 2

seeds:
  - name: ciclo_cultura
    columns:
      - name: cultura
        tests: [not_null, unique]
      - name: mes_inicio
        tests:
          - dbt_utils.accepted_range:
              min_value: 1
              max_value: 12
```

- [ ] **Step 2: Escrever os testes dbt que falham**

Acrescentar a `dbt/models/staging/schema.yml`:

```yaml
  - name: dim_uf
    columns:
      - name: uf
        tests: [not_null, unique]
      - name: uf_codigo
        tests: [not_null, unique]

  - name: dim_cultura
    columns:
      - name: cultura
        tests: [not_null, unique]
```

- [ ] **Step 3: Rodar e confirmar que falha**

Run: `cd dbt && dbt build --select dim_uf dim_cultura ciclo_cultura`
Expected: FAIL — modelos não existem

- [ ] **Step 4: Implementar**

```sql
-- dbt/models/staging/dim_uf.sql
with codigos as (
    select * from (values
        ('11','RO','Rondonia','Norte'), ('12','AC','Acre','Norte'),
        ('13','AM','Amazonas','Norte'), ('14','RR','Roraima','Norte'),
        ('15','PA','Para','Norte'), ('16','AP','Amapa','Norte'),
        ('17','TO','Tocantins','Norte'), ('21','MA','Maranhao','Nordeste'),
        ('22','PI','Piaui','Nordeste'), ('23','CE','Ceara','Nordeste'),
        ('24','RN','Rio Grande do Norte','Nordeste'), ('25','PB','Paraiba','Nordeste'),
        ('26','PE','Pernambuco','Nordeste'), ('27','AL','Alagoas','Nordeste'),
        ('28','SE','Sergipe','Nordeste'), ('29','BA','Bahia','Nordeste'),
        ('31','MG','Minas Gerais','Sudeste'), ('32','ES','Espirito Santo','Sudeste'),
        ('33','RJ','Rio de Janeiro','Sudeste'), ('35','SP','Sao Paulo','Sudeste'),
        ('41','PR','Parana','Sul'), ('42','SC','Santa Catarina','Sul'),
        ('43','RS','Rio Grande do Sul','Sul'), ('50','MS','Mato Grosso do Sul','Centro-Oeste'),
        ('51','MT','Mato Grosso','Centro-Oeste'), ('52','GO','Goias','Centro-Oeste'),
        ('53','DF','Distrito Federal','Centro-Oeste')
    ) as t(uf_codigo, uf, uf_nome, regiao)
)
select * from codigos
```

```sql
-- dbt/models/staging/dim_cultura.sql
select * from (values
    ('soja',  'Soja'),
    ('milho', 'Milho'),
    ('cafe',  'Cafe'),
    ('cana',  'Cana-de-acucar')
) as t(cultura, nome_exibicao)
```

- [ ] **Step 5: Rodar e confirmar que passa**

Run: `cd dbt && dbt build --select dim_uf dim_cultura ciclo_cultura`
Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add dbt/seeds dbt/models/staging/dim_uf.sql dbt/models/staging/dim_cultura.sql dbt/models/staging/schema.yml
git commit -m "Add UF and crop dimensions with cycle seed"
```

---

### Task 9: Camada Gold

**Files:**
- Create: `dbt/models/marts/gold_clima_uf_mensal.sql`
- Create: `dbt/models/marts/gold_safra_uf.sql`
- Create: `dbt/models/marts/gold_clima_safra.sql`
- Create: `dbt/models/marts/schema.yml`

**Interfaces:**
- Consumes: `stg_clima_diario`, `stg_pam`, `dim_uf`, `dim_cultura`, `ciclo_cultura`
- Produces:
  - `gold_clima_uf_mensal(uf, ano, mes, temp_media, temp_max, temp_min, precipitacao, dias_sem_chuva, n_estacoes, temp_media_movel_3m, anomalia_temp, anomalia_precip)`
  - `gold_safra_uf(uf, uf_codigo, cultura, ano, area_plantada, area_colhida, producao, rendimento, var_producao_aa, var_rendimento_aa)`
  - `gold_clima_safra(uf, cultura, ano, rendimento, precip_ciclo, temp_media_ciclo, n_estacoes)`

- [ ] **Step 1: Escrever os testes dbt que falham**

```yaml
# dbt/models/marts/schema.yml
version: 2

models:
  - name: gold_clima_uf_mensal
    tests:
      - dbt_utils.unique_combination_of_columns:
          combination_of_columns: [uf, ano, mes]
    columns:
      - name: n_estacoes
        tests:
          - dbt_utils.accepted_range:
              min_value: 1
      - name: precipitacao
        tests:
          - dbt_utils.accepted_range:
              min_value: 0

  - name: gold_safra_uf
    tests:
      - dbt_utils.unique_combination_of_columns:
          combination_of_columns: [uf, cultura, ano]
    columns:
      - name: uf
        tests:
          - relationships:
              to: ref('dim_uf')
              field: uf
      - name: cultura
        tests:
          - relationships:
              to: ref('dim_cultura')
              field: cultura

  - name: gold_clima_safra
    columns:
      - name: rendimento
        tests:
          - dbt_utils.accepted_range:
              min_value: 0
              severity: warn
```

- [ ] **Step 2: Rodar e confirmar que falha**

Run: `cd dbt && dbt build --select marts`
Expected: FAIL — modelos não existem

- [ ] **Step 3: Implementar gold_clima_uf_mensal**

```sql
-- dbt/models/marts/gold_clima_uf_mensal.sql
with mensal as (
    select
        uf,
        year(data)  as ano,
        month(data) as mes,
        avg(temp_media)                          as temp_media,
        max(temp_max)                            as temp_max,
        min(temp_min)                            as temp_min,
        sum(precipitacao)                        as precipitacao,
        count(distinct case when precipitacao = 0 then data end) as dias_sem_chuva,
        count(distinct cd_estacao)               as n_estacoes
    from {{ ref('stg_clima_diario') }}
    group by 1, 2, 3
),

normais as (
    select uf, mes, avg(temp_media) as temp_normal, avg(precipitacao) as precip_normal
    from mensal
    group by 1, 2
)

select
    m.uf,
    m.ano,
    m.mes,
    m.temp_media,
    m.temp_max,
    m.temp_min,
    m.precipitacao,
    m.dias_sem_chuva,
    m.n_estacoes,
    avg(m.temp_media) over (
        partition by m.uf order by m.ano, m.mes rows between 2 preceding and current row
    ) as temp_media_movel_3m,
    m.temp_media - n.temp_normal     as anomalia_temp,
    m.precipitacao - n.precip_normal as anomalia_precip
from mensal m
inner join normais n on n.uf = m.uf and n.mes = m.mes
```

- [ ] **Step 4: Implementar gold_safra_uf**

```sql
-- dbt/models/marts/gold_safra_uf.sql
with base as (
    select
        d.uf,
        p.uf_codigo,
        p.cultura,
        p.ano,
        p.area_plantada,
        p.area_colhida,
        p.producao,
        p.rendimento
    from {{ ref('stg_pam') }} p
    inner join {{ ref('dim_uf') }} d on d.uf_codigo = p.uf_codigo
)

select
    *,
    100.0 * (producao / nullif(lag(producao) over (partition by uf, cultura order by ano), 0) - 1)
        as var_producao_aa,
    100.0 * (rendimento / nullif(lag(rendimento) over (partition by uf, cultura order by ano), 0) - 1)
        as var_rendimento_aa
from base
```

- [ ] **Step 5: Implementar gold_clima_safra**

```sql
-- dbt/models/marts/gold_clima_safra.sql
with ciclo as (
    select * from {{ ref('ciclo_cultura') }}
),

meses_do_ciclo as (
    select
        c.cultura,
        m.uf,
        case when c.mes_inicio > c.mes_fim and m.mes >= c.mes_inicio
             then m.ano + 1
             else m.ano
        end as ano_safra,
        m.precipitacao,
        m.temp_media,
        m.n_estacoes
    from {{ ref('gold_clima_uf_mensal') }} m
    cross join ciclo c
    where (c.mes_inicio <= c.mes_fim and m.mes between c.mes_inicio and c.mes_fim)
       or (c.mes_inicio >  c.mes_fim and (m.mes >= c.mes_inicio or m.mes <= c.mes_fim))
),

agregado as (
    select
        uf,
        cultura,
        ano_safra as ano,
        sum(precipitacao) as precip_ciclo,
        avg(temp_media)   as temp_media_ciclo,
        min(n_estacoes)   as n_estacoes
    from meses_do_ciclo
    group by 1, 2, 3
)

select
    s.uf,
    s.cultura,
    s.ano,
    s.rendimento,
    a.precip_ciclo,
    a.temp_media_ciclo,
    a.n_estacoes
from {{ ref('gold_safra_uf') }} s
inner join agregado a on a.uf = s.uf and a.cultura = s.cultura and a.ano = s.ano
where s.rendimento is not null
```

- [ ] **Step 6: Rodar e confirmar que passa**

Run: `cd dbt && dbt build --select marts`
Expected: PASS

- [ ] **Step 7: Commit**

```bash
git add dbt/models/marts
git commit -m "Add gold models for climate, harvest and their crossing"
```

---

### Task 10: Teste singular de reconciliação do milho

**Files:**
- Create: `dbt/tests/milho_lspa_bate_com_pam.sql`

**Interfaces:**
- Consumes: `stg_lspa`, `stg_pam`
- Produces: nada (teste)

- [ ] **Step 1: Escrever o teste**

Um teste singular do dbt passa quando não retorna linhas.

```sql
-- dbt/tests/milho_lspa_bate_com_pam.sql
with lspa_anual as (
    select uf_codigo, ano, sum(producao) as producao_lspa
    from {{ ref('stg_lspa') }}
    where cultura = 'milho' and mes = 12
    group by 1, 2
),

pam_anual as (
    select uf_codigo, ano, producao as producao_pam
    from {{ ref('stg_pam') }}
    where cultura = 'milho'
)

select
    p.uf_codigo,
    p.ano,
    p.producao_pam,
    l.producao_lspa,
    abs(l.producao_lspa - p.producao_pam) / nullif(p.producao_pam, 0) as divergencia
from pam_anual p
inner join lspa_anual l on l.uf_codigo = p.uf_codigo and l.ano = p.ano
where p.producao_pam > 0
  and abs(l.producao_lspa - p.producao_pam) / p.producao_pam > 0.15
```

- [ ] **Step 2: Rodar**

Run: `cd dbt && dbt test --select milho_lspa_bate_com_pam`
Expected: PASS

Se falhar, inspecionar as linhas retornadas antes de afrouxar o limite de
15%: pode indicar erro no mapeamento de ciclo, não ruído da fonte.

- [ ] **Step 3: Commit**

```bash
git add dbt/tests
git commit -m "Check LSPA maize cycles reconcile with PAM totals"
```

---

### Task 11: Acesso a dados do dashboard

**Files:**
- Create: `dashboard/__init__.py`, `dashboard/data.py`
- Test: `tests/test_dashboard_data.py`

**Interfaces:**
- Consumes: `config.DUCKDB_PATH`
- Produces:
  - `data.consultar(sql: str, params: list | None = None) -> pd.DataFrame`
  - `data.clima_mensal(ufs, ano_ini, ano_fim) -> pd.DataFrame`
  - `data.safra(ufs, culturas) -> pd.DataFrame`
  - `data.clima_safra(culturas) -> pd.DataFrame`

- [ ] **Step 1: Escrever o teste que falha**

```python
# tests/test_dashboard_data.py
import duckdb
import pytest

from dashboard import data


@pytest.fixture
def banco(tmp_path, monkeypatch):
    caminho = tmp_path / "w.duckdb"
    con = duckdb.connect(str(caminho))
    con.execute("create table gold_safra_uf (uf varchar, cultura varchar, ano integer, producao double)")
    con.execute("insert into gold_safra_uf values ('PR','soja',2024,18689393), ('MT','soja',2024,38396410)")
    con.close()
    monkeypatch.setattr(data.config, "DUCKDB_PATH", caminho)
    return caminho


def test_consultar_retorna_dataframe(banco):
    df = data.consultar("select * from gold_safra_uf order by uf")
    assert list(df["uf"]) == ["MT", "PR"]


def test_consultar_aceita_parametros(banco):
    df = data.consultar("select * from gold_safra_uf where uf = ?", ["PR"])
    assert len(df) == 1


def test_consultar_nao_deixa_conexao_aberta(banco):
    data.consultar("select 1")
    duckdb.connect(str(banco)).close()
```

O terceiro teste é o que importa: prova que a conexão fecha e que outro
processo consegue abrir o banco em seguida.

- [ ] **Step 2: Rodar e confirmar que falha**

Run: `python -m pytest tests/test_dashboard_data.py -v`
Expected: FAIL com `ModuleNotFoundError: No module named 'dashboard'`

- [ ] **Step 3: Implementar**

```python
# dashboard/data.py
import time

import duckdb
import pandas as pd
import streamlit as st

from src import config


def consultar(sql: str, params: list | None = None) -> pd.DataFrame:
    for tentativa in range(3):
        try:
            con = duckdb.connect(str(config.DUCKDB_PATH), read_only=True)
            try:
                return con.execute(sql, params or []).fetch_df()
            finally:
                con.close()
        except duckdb.IOException:
            if tentativa == 2:
                raise
            time.sleep(1)


@st.cache_data(ttl=600)
def clima_mensal(ufs: tuple[str, ...], ano_ini: int, ano_fim: int) -> pd.DataFrame:
    marcadores = ", ".join("?" for _ in ufs)
    return consultar(
        f"""
        select * from gold_clima_uf_mensal
        where uf in ({marcadores}) and ano between ? and ?
        order by ano, mes
        """,
        list(ufs) + [ano_ini, ano_fim],
    )


@st.cache_data(ttl=600)
def safra(ufs: tuple[str, ...], culturas: tuple[str, ...]) -> pd.DataFrame:
    m_uf = ", ".join("?" for _ in ufs)
    m_cult = ", ".join("?" for _ in culturas)
    return consultar(
        f"select * from gold_safra_uf where uf in ({m_uf}) and cultura in ({m_cult}) order by ano",
        list(ufs) + list(culturas),
    )


@st.cache_data(ttl=600)
def clima_safra(culturas: tuple[str, ...]) -> pd.DataFrame:
    marcadores = ", ".join("?" for _ in culturas)
    return consultar(
        f"select * from gold_clima_safra where cultura in ({marcadores})",
        list(culturas),
    )
```

O retry cobre o caso real de lock durante a janela de escrita das 06h.

- [ ] **Step 4: Rodar e confirmar que passa**

Run: `python -m pytest tests/test_dashboard_data.py -v`
Expected: PASS (3 testes)

- [ ] **Step 5: Commit**

```bash
git add dashboard tests/test_dashboard_data.py
git commit -m "Add read-only DuckDB access layer for the dashboard"
```

---

### Task 12: Páginas do dashboard

**Files:**
- Create: `dashboard/app.py`
- Create: `dashboard/views/__init__.py`, `overview.py`, `clima.py`, `safra.py`, `clima_safra.py`
- Create: `.streamlit/config.toml`

**Interfaces:**
- Consumes: `dashboard.data`
- Produces: aplicação Streamlit; cada view expõe `render(filtros: dict) -> None`

- [ ] **Step 1: Criar a configuração do Streamlit**

```toml
# .streamlit/config.toml
[theme]
base = "light"
primaryColor = "#2e7d32"

[server]
headless = true
port = 8501
```

- [ ] **Step 2: Implementar o app e as views**

```python
# dashboard/app.py
import streamlit as st

from dashboard import data
from dashboard.views import clima, clima_safra, overview, safra

st.set_page_config(page_title="AgroClima Analytics", layout="wide")

PAGINAS = {
    "Visao geral": overview,
    "Clima": clima,
    "Safra": safra,
    "Clima x Safra": clima_safra,
}

UFS = [
    "AC","AL","AP","AM","BA","CE","DF","ES","GO","MA","MT","MS","MG","PA",
    "PB","PR","PE","PI","RJ","RN","RS","RO","RR","SC","SP","SE","TO",
]
CULTURAS = ["soja", "milho", "cafe", "cana"]

st.sidebar.title("AgroClima")
pagina = st.sidebar.radio("Pagina", list(PAGINAS))

filtros = {
    "ufs": tuple(st.sidebar.multiselect("UF", UFS, default=["MT", "PR", "RS"])),
    "culturas": tuple(st.sidebar.multiselect("Cultura", CULTURAS, default=["soja"])),
    "ano_ini": st.sidebar.number_input("Ano inicial", 2022, 2026, 2022),
    "ano_fim": st.sidebar.number_input("Ano final", 2022, 2026, 2026),
}

if not filtros["ufs"] or not filtros["culturas"]:
    st.warning("Selecione ao menos uma UF e uma cultura.")
else:
    PAGINAS[pagina].render(filtros)
```

```python
# dashboard/views/overview.py
import plotly.express as px
import streamlit as st

from dashboard import data

GEOJSON = "https://servicodados.ibge.gov.br/api/v3/malhas/paises/BR?formato=application/vnd.geo+json&qualidade=intermediaria&intrarregiao=UF"


def render(filtros):
    st.header("Visao geral")

    df = data.safra(filtros["ufs"], filtros["culturas"])
    if df.empty:
        st.info("Sem dados para os filtros selecionados.")
        return

    ultimo = df[df["ano"] == df["ano"].max()]
    col1, col2, col3 = st.columns(3)
    col1.metric("Producao total (t)", f"{ultimo['producao'].sum():,.0f}")
    col2.metric("Rendimento medio (kg/ha)", f"{ultimo['rendimento'].mean():,.0f}")
    col3.metric("Area colhida (ha)", f"{ultimo['area_colhida'].sum():,.0f}")

    st.subheader(f"Producao por UF em {int(df['ano'].max())}")
    fig = px.bar(ultimo.sort_values("producao"), x="producao", y="uf", color="cultura", orientation="h")
    st.plotly_chart(fig, use_container_width=True)
```

```python
# dashboard/views/clima.py
import plotly.express as px
import streamlit as st

from dashboard import data


def render(filtros):
    st.header("Clima")

    df = data.clima_mensal(filtros["ufs"], filtros["ano_ini"], filtros["ano_fim"])
    if df.empty:
        st.info("Sem dados para os filtros selecionados.")
        return

    df["competencia"] = df["ano"].astype(str) + "-" + df["mes"].astype(str).str.zfill(2)

    st.subheader("Temperatura media e media movel de 3 meses")
    fig = px.line(df, x="competencia", y=["temp_media", "temp_media_movel_3m"], color="uf")
    st.plotly_chart(fig, use_container_width=True)

    st.subheader("Precipitacao acumulada")
    st.plotly_chart(px.bar(df, x="competencia", y="precipitacao", color="uf"), use_container_width=True)

    st.subheader("Anomalia de temperatura")
    st.plotly_chart(px.line(df, x="competencia", y="anomalia_temp", color="uf"), use_container_width=True)

    st.caption("n_estacoes indica quantas estacoes contribuiram para cada ponto.")
    st.dataframe(df[["uf", "competencia", "n_estacoes", "temp_media", "precipitacao"]])
```

```python
# dashboard/views/safra.py
import plotly.express as px
import streamlit as st

from dashboard import data


def render(filtros):
    st.header("Safra")

    df = data.safra(filtros["ufs"], filtros["culturas"])
    if df.empty:
        st.info("Sem dados para os filtros selecionados.")
        return

    st.subheader("Producao por ano")
    st.plotly_chart(px.line(df, x="ano", y="producao", color="uf", line_dash="cultura"), use_container_width=True)

    st.subheader("Rendimento (kg/ha)")
    st.plotly_chart(px.line(df, x="ano", y="rendimento", color="uf", line_dash="cultura"), use_container_width=True)

    st.subheader("Variacao anual da producao (%)")
    st.plotly_chart(px.bar(df, x="ano", y="var_producao_aa", color="uf"), use_container_width=True)
```

```python
# dashboard/views/clima_safra.py
import plotly.express as px
import streamlit as st

from dashboard import data


def render(filtros):
    st.header("Clima x Safra")

    df = data.clima_safra(filtros["culturas"])
    df = df[df["uf"].isin(filtros["ufs"])]
    if df.empty:
        st.info("Sem dados para os filtros selecionados.")
        return

    eixo = st.radio("Variavel climatica", ["precip_ciclo", "temp_media_ciclo"], horizontal=True)

    fig = px.scatter(
        df, x=eixo, y="rendimento", color="uf", symbol="cultura",
        trendline="ols", hover_data=["ano", "n_estacoes"],
    )
    st.plotly_chart(fig, use_container_width=True)

    st.subheader("Correlacao por cultura")
    correl = (
        df.groupby("cultura")[[eixo, "rendimento"]]
        .corr().unstack().iloc[:, 1].rename("correlacao").reset_index()
    )
    st.dataframe(correl)
```

`trendline="ols"` exige `statsmodels`. Acrescentar ao `requirements.txt`:

```
statsmodels==0.14.4
```

- [ ] **Step 3: Verificar que o app sobe**

Run: `streamlit run dashboard/app.py`
Expected: abre em http://localhost:8501 sem erro de importação. Com o banco
vazio, cada página mostra "Sem dados para os filtros selecionados."

- [ ] **Step 4: Commit**

```bash
git add dashboard .streamlit requirements.txt
git commit -m "Add Streamlit dashboard with four pages"
```

---

### Task 13: DAG do Airflow

**Files:**
- Create: `airflow/dags/agroclima_pipeline_dag.py`
- Test: `tests/test_dag.py`

**Interfaces:**
- Consumes: `pipeline.ingerir`, `pipeline.rodar_dbt`
- Produces: DAG `agroclima_pipeline`

- [ ] **Step 1: Escrever o teste que falha**

Este teste só roda onde o Airflow está instalado (Docker), então é marcado
para pular fora dele.

```python
# tests/test_dag.py
import pytest

airflow = pytest.importorskip("airflow")

from airflow.models import DagBag


def test_dag_carrega_sem_erro():
    bag = DagBag(dag_folder="airflow/dags", include_examples=False)
    assert bag.import_errors == {}
    assert "agroclima_pipeline" in bag.dags


def test_dag_tem_as_tarefas_esperadas():
    bag = DagBag(dag_folder="airflow/dags", include_examples=False)
    tarefas = set(bag.dags["agroclima_pipeline"].task_ids)
    assert tarefas == {
        "start", "ingest_inmet_estacoes", "ingest_inmet_clima",
        "ingest_sidra", "dbt_build", "notify", "end",
    }


def test_ingestoes_rodam_em_paralelo_antes_do_dbt():
    dag = DagBag(dag_folder="airflow/dags", include_examples=False).dags["agroclima_pipeline"]
    assert dag.get_task("dbt_build").upstream_task_ids == {
        "ingest_inmet_estacoes", "ingest_inmet_clima", "ingest_sidra",
    }
```

- [ ] **Step 2: Rodar e confirmar que falha ou pula**

Run: `python -m pytest tests/test_dag.py -v`
Expected: SKIPPED no Windows (sem Airflow); FAIL no Docker antes da implementação

- [ ] **Step 3: Implementar**

```python
# airflow/dags/agroclima_pipeline_dag.py
from datetime import datetime, timedelta

from airflow import DAG
from airflow.operators.empty import EmptyOperator
from airflow.operators.python import PythonOperator

from src import config
from src.ingestion import inmet_api, sidra_api
from src.pipeline import rodar_dbt

default_args = {
    "owner": "antoniolaprov",
    "retries": 2,
    "retry_delay": timedelta(minutes=5),
}


def _clima():
    return inmet_api.ingest_clima(config.ANOS_CLIMA)


def _notificar(**contexto):
    ti = contexto["ti"]
    print("estacoes:", ti.xcom_pull(task_ids="ingest_inmet_estacoes"))
    print("clima:", ti.xcom_pull(task_ids="ingest_inmet_clima"))
    print("sidra:", ti.xcom_pull(task_ids="ingest_sidra"))


with DAG(
    dag_id="agroclima_pipeline",
    default_args=default_args,
    start_date=datetime(2026, 1, 1),
    schedule="0 9 * * *",
    catchup=False,
    max_active_runs=1,
    tags=["agroclima"],
) as dag:
    start = EmptyOperator(task_id="start")

    estacoes = PythonOperator(
        task_id="ingest_inmet_estacoes",
        python_callable=inmet_api.ingest_estacoes,
    )
    clima = PythonOperator(task_id="ingest_inmet_clima", python_callable=_clima)
    sidra = PythonOperator(
        task_id="ingest_sidra",
        python_callable=lambda: {"pam": sidra_api.ingest_pam(), "lspa": sidra_api.ingest_lspa()},
    )

    dbt = PythonOperator(task_id="dbt_build", python_callable=rodar_dbt)
    notify = PythonOperator(task_id="notify", python_callable=_notificar)
    end = EmptyOperator(task_id="end")

    start >> [estacoes, clima, sidra] >> dbt >> notify >> end
```

O horário `0 9 * * *` é 09h UTC, que corresponde a 06h BRT.

- [ ] **Step 4: Commit**

```bash
git add airflow tests/test_dag.py
git commit -m "Add daily Airflow DAG for the pipeline"
```

---

### Task 14: Docker, Makefile e README

**Files:**
- Create: `docker-compose.yml`, `Dockerfile`, `dashboard/Dockerfile`
- Create: `Makefile`, `.env.example`, `README.md`

**Interfaces:**
- Consumes: tudo anterior
- Produces: `docker compose up -d` sobe Airflow em `:8080` e dashboard em `:8501`

- [ ] **Step 1: Criar os Dockerfiles**

```dockerfile
# Dockerfile (Airflow + pipeline)
FROM apache/airflow:2.10.3-python3.12

USER root
RUN apt-get update && apt-get install -y --no-install-recommends git && rm -rf /var/lib/apt/lists/*
USER airflow

COPY requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt

ENV PYTHONPATH=/opt/airflow
```

```dockerfile
# dashboard/Dockerfile
FROM python:3.12-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src ./src
COPY dashboard ./dashboard
COPY .streamlit ./.streamlit

EXPOSE 8501
CMD ["streamlit", "run", "dashboard/app.py", "--server.address=0.0.0.0"]
```

- [ ] **Step 2: Criar o compose**

```yaml
# docker-compose.yml
services:
  airflow:
    build: .
    command: standalone
    environment:
      AIRFLOW__CORE__LOAD_EXAMPLES: "false"
      AIRFLOW__CORE__DAGS_FOLDER: /opt/airflow/airflow/dags
      _AIRFLOW_WWW_USER_USERNAME: ${AIRFLOW_USER:-admin}
      _AIRFLOW_WWW_USER_PASSWORD: ${AIRFLOW_PASSWORD:-admin}
    volumes:
      - ./airflow:/opt/airflow/airflow
      - ./src:/opt/airflow/src
      - ./dbt:/opt/airflow/dbt
      - ./data:/opt/airflow/data
    ports:
      - "8080:8080"

  dashboard:
    build:
      context: .
      dockerfile: dashboard/Dockerfile
    volumes:
      - ./data:/app/data
    ports:
      - "8501:8501"
    depends_on:
      - airflow
```

```
# .env.example
AIRFLOW_USER=admin
AIRFLOW_PASSWORD=admin
```

A senha do Airflow vem do `.env`, que está no `.gitignore`. O
`.env.example` traz só o valor padrão de desenvolvimento.

- [ ] **Step 3: Criar o Makefile**

```makefile
.PHONY: install test pipeline dashboard dbt up down

install:
	pip install -r requirements.txt
	cd dbt && dbt deps

test:
	python -m pytest -v

pipeline:
	python -m src.pipeline

dbt:
	cd dbt && dbt build

dashboard:
	streamlit run dashboard/app.py

up:
	docker compose up -d

down:
	docker compose down
```

- [ ] **Step 4: Escrever o README**

Conteúdo mínimo, sem prosa de marketing:

```markdown
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

O Airflow agenda o processo todo dia as 06h.

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
cd dbt && dbt deps && cd ..

python -m src.pipeline
streamlit run dashboard/app.py
```

Acesse: http://localhost:8501

A primeira execucao baixa cerca de 300 MB do INMET e leva alguns minutos. As
seguintes verificam o ETag do arquivo e so baixam o que mudou.

O Airflow nao roda nativamente no Windows; use o Docker para a parte de
agendamento.

### Com Docker (inclui Airflow)

```
cp .env.example .env
docker compose up -d
```

- Dashboard: http://localhost:8501
- Airflow: http://localhost:8080

## Estrutura

- `src/ingestion` - clientes das APIs, gravam Parquet em `data/bronze`
- `dbt/models/staging` - limpeza e padronizacao (Silver)
- `dbt/models/marts` - KPIs e cruzamentos (Gold)
- `dashboard` - aplicacao Streamlit
- `airflow/dags` - agendamento

## Limitacoes conhecidas

- A media climatica por estado nao e ponderada por area: estados grandes tem
  cobertura desigual de estacoes. O campo `n_estacoes` fica visivel no
  dashboard para o leitor julgar cada ponto.
- A API horaria do INMET (`apitempo`) esta fechada e retorna 204; o projeto
  usa os arquivos anuais de dados historicos, atualizados a cada ~90 dias.

## Fontes

- [INMET Dados Historicos](https://portal.inmet.gov.br/dadoshistoricos)
- [IBGE API de agregados](https://servicodados.ibge.gov.br/api/docs/agregados?versao=3)
```

- [ ] **Step 5: Verificar que o compose sobe**

Run: `docker compose up -d --build` e depois `docker compose ps`
Expected: os dois serviços em estado `running`; Airflow responde em `:8080`

- [ ] **Step 6: Rodar a suíte inteira**

Run: `python -m pytest -v`
Expected: todos passam (testes de DAG pulados no Windows)

- [ ] **Step 7: Commit**

```bash
git add Dockerfile dashboard/Dockerfile docker-compose.yml Makefile .env.example README.md
git commit -m "Add Docker setup, Makefile and README"
```

---

## Self-Review

**Cobertura da spec:**

| Seção da spec | Tarefa |
|---|---|
| 3 — Python ingere, dbt transforma | 1-6 (Python), 7-10 (dbt) |
| 4.1 — estações INMET | 2 |
| 4.1 — CSV horário, latin1, sentinelas | 3 |
| 4.1 — ZIP condicional, manifest | 4 |
| 4.2 — PAM e LSPA, milho 1ª/2ª safra | 5, 10 |
| 5.1 — Bronze, `_ingested_at`, `_source_url` | 1, 2, 4, 5 |
| 5.2 — Silver, corte de 18 horas | 7 |
| 5.3 — Gold, anomalia, média móvel, ciclo | 8, 9 |
| 6 — qualidade via testes dbt | 7, 8, 9, 10 |
| 7 — DAG diária, ingestões em paralelo | 13 |
| 8 — dashboard, 4 páginas, retry no DuckDB | 11, 12 |
| 9 — estrutura de pastas | todas |
| 10 — testes | 1-6, 11, 13 |
| 12 — execução local e Docker | 14 |

**Lacuna encontrada e corrigida:** a spec menciona mapa coroplético com
GeoJSON do IBGE na página de visão geral. A Task 12 define a constante
`GEOJSON` mas usa gráfico de barras, porque o `px.choropleth_mapbox` exige
casar a chave do GeoJSON (código de UF) com a sigla, o que depende de
inspecionar a malha em tempo de implementação. **Decisão:** entregar barras
primeiro e trocar por mapa em um passo seguinte, quando a estrutura real do
GeoJSON estiver à mão. Registrar como pendência, não como entregue.

**Consistência de tipos:** `parse_csv_estacao(conteudo: bytes, nome_arquivo: str)`
tem a mesma assinatura na Task 3 e na chamada da Task 4. `ingest_clima(anos)`
devolve `dict[int, int]` na Task 4, e a Task 6 trata como dicionário.
`config.BRONZE_DIR` é lido via `base.config` nos testes da Task 1, o que
exige que `base` importe o módulo `config` inteiro — está assim na
implementação.

**Sem placeholders:** nenhum TBD ou TODO. Todos os passos de código trazem
o conteúdo real.
