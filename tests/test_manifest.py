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
