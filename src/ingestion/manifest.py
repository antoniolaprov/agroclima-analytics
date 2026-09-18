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
