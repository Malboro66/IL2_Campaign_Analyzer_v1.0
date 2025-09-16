import pytest
from pathlib import Path
from app.core.data_parser import IL2DataParser

def test_get_campaigns_returns_list(tmp_path):
    # cria estrutura de campanhas fake
    campaigns_dir = tmp_path / "User" / "Campaigns"
    campaigns_dir.mkdir(parents=True)
    (campaigns_dir / "Campanha1").mkdir()
    (campaigns_dir / "Campanha2").mkdir()

    parser = IL2DataParser(tmp_path)
    campaigns = parser.get_campaigns()

    assert "Campanha1" in campaigns
    assert "Campanha2" in campaigns
    assert isinstance(campaigns, list)

def test_get_json_data_handles_invalid_file(tmp_path):
    parser = IL2DataParser(tmp_path)
    result = parser.get_json_data(tmp_path / "nao_existe.json")
    assert result is None
