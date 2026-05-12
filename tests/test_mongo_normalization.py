from backend.mongo_service import MongoService


def test_normalize_data_entry_handles_missing_fields():
    e = MongoService._normalize_data_entry({"type": "raw_records"})
    assert e.data_type == "raw_records"
    assert e.host is None
    assert e.location is None
    assert e.lineage_hash is None
