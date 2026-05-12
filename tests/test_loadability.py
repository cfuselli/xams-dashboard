from backend.loadability import assess_loadability
from backend.models import DataEntry, RunDetails


def test_assess_loadability_basic():
    rd = RunDetails(
        number=1,
        mode="m",
        start=None,
        end=None,
        tags=[],
        comments=[],
        processing_status=None,
        raw_doc={},
        data_entries=[
            DataEntry("events", "wn", "/tmp/events", "abc123", "2.1.0", {}),
            DataEntry("peaks", "wn", None, None, None, {}),
        ],
    )
    rows = assess_loadability(rd)
    assert len(rows) == 2
    assert rows[0]["type"] == "events"
    assert rows[0]["loadable"] is True
    assert rows[1]["loadable"] is False
