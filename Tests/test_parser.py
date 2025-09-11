import json
from pathlib import Path
import pytest
from main_app import IL2DataParser

@pytest.mark.parametrize("as_str", [False, True])
def test_get_json_data(tmp_path: Path, as_str: bool):
    """Verify JSON file is read correctly when passed as Path or str."""
    payload = {"key": "value"}
    file = tmp_path / "test.json"
    file.write_text(json.dumps(payload), encoding="utf-8")

    parser = IL2DataParser(tmp_path)
    arg = str(file) if as_str else file
    data = parser.get_json_data(arg)

    assert isinstance(data, dict)
    assert data == payload

def test_get_json_data_invalid_json(tmp_path: Path):
    """Invalid JSON should raise a JSON decode / ValueError."""
    file = tmp_path / "bad.json"
    file.write_text("{ not: valid json }", encoding="utf-8")

    parser = IL2DataParser(tmp_path)
    with pytest.raises((ValueError, json.JSONDecodeError)):
        parser.get_json_data(file)

def test_get_campaigns(tmp_path: Path):
    """Create multiple campaign folders and ensure they are discovered."""
    (tmp_path / "User" / "Campaigns" / "Camp1").mkdir(parents=True)
    (tmp_path / "User" / "Campaigns" / "Camp2").mkdir(parents=True)

    parser = IL2DataParser(tmp_path)
    campaigns = parser.get_campaigns()

    assert isinstance(campaigns, (list, tuple))
    assert {"Camp1", "Camp2"}.issubset(set(campaigns))

def test_get_campaigns_no_campaigns_returns_empty(tmp_path: Path):
    """If the Campaigns folder is missing or empty, return an empty list (not raise)."""
    # do not create User/Campaigns at all
    parser = IL2DataParser(tmp_path)
    campaigns = parser.get_campaigns()
    assert campaigns == [] or campaigns == []
