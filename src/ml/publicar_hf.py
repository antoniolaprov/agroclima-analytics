"""Publica a versao atual do modelo no Hugging Face Hub.

Uso: HF_TOKEN=... python -m src.ml.publicar_hf --repo usuario/agroclima-anomalia-rendimento

O token precisa de permissao de escrita (https://huggingface.co/settings/tokens).
Sobe o model card (README.md), os modelos, as metricas, as figuras e os
metadados; as previsoes do backtest ficam de fora por tamanho.
"""

import argparse
import json
import os
from pathlib import Path

from src.ml.treino import MODELOS_DIR

PADROES = ["README.md", "relatorio.md", "metadados.json", "*.joblib", "metricas*.csv",
           "importancia.csv", "figuras/*.png"]


def publicar(repo: str, pasta: Path = MODELOS_DIR / "atual", privado: bool = False) -> str:
    from huggingface_hub import HfApi

    if not (pasta / "README.md").exists():
        raise FileNotFoundError(f"nenhum modelo treinado em {pasta}")
    token = os.environ.get("HF_TOKEN")
    if not token:
        raise RuntimeError("defina HF_TOKEN com um token de escrita do Hugging Face")

    versao = json.loads((pasta / "metadados.json").read_text(encoding="utf-8"))["versao"]
    api = HfApi(token=token)
    api.create_repo(repo, repo_type="model", private=privado, exist_ok=True)
    info = api.upload_folder(
        repo_id=repo,
        folder_path=str(pasta),
        allow_patterns=PADROES,
        commit_message=f"Model version {versao}",
    )
    return info.commit_url


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--repo", required=True)
    p.add_argument("--pasta", type=Path, default=MODELOS_DIR / "atual")
    p.add_argument("--privado", action="store_true")
    a = p.parse_args()
    print(publicar(a.repo, a.pasta, a.privado))
