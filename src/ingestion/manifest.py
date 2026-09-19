import json

from src import config

CAMINHO = config.BRONZE_DIR / "_manifest.json"


def _carregar() -> dict:
    if not CAMINHO.exists():
        return {}
    return json.loads(CAMINHO.read_text(encoding="utf-8"))


def ler(chave: str) -> dict | None:
    return _carregar().get(chave)


def gravar(chave: str, dados: dict) -> None:
    tudo = _carregar()
    tudo[chave] = dados
    CAMINHO.parent.mkdir(parents=True, exist_ok=True)
    CAMINHO.write_text(json.dumps(tudo, indent=2), encoding="utf-8")
