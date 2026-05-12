from backend.processing_service import ProcessingService


def test_submit_run_failure_when_command_missing(tmp_path):
    svc = ProcessingService(
        amstrax_dir=str(tmp_path / "missing"),
        log_dir=str(tmp_path / "logs"),
        output_dir=str(tmp_path / "out"),
    )
    out = svc.submit_run(1234, target="events")
    assert out["submitted"] is False
    assert out["returncode"] != 0
