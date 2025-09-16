from app.core.data_processor import IL2DataProcessor

def test_process_empty_campaign_returns_dict():
    processor = IL2DataProcessor("/caminho/invalido")
    result = processor.process_campaign("CampanhaFake")
    assert isinstance(result, dict)
    assert "pilot" in result
    assert "missions" in result
    assert "squadron" in result
    assert "aces" in result
