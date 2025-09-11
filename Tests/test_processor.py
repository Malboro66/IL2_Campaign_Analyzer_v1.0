import pytest
from main_app import IL2DataProcessor

@pytest.mark.parametrize("path_type", ("path", "str"))
def test_process_empty_campaign(tmp_path, path_type):
    """
    Ensure process_campaign returns an empty dict for a campaign that doesn't exist.
    This also checks the processor accepts both pathlib.Path and str path arguments.
    """
    base = tmp_path if path_type == "path" else str(tmp_path)
    processor = IL2DataProcessor(base)

    result = processor.process_campaign("Inexistente")

    assert isinstance(result, dict), "process_campaign must return a dict"
    assert result == {}, "nonexistent campaign should yield an empty dict"
