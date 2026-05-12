from __future__ import annotations

import os
import subprocess
from datetime import datetime
import time
from typing import Dict, List, Union

from .config import settings


class ProcessingService:
    def __init__(self, amstrax_dir: str  = None, log_dir: str  = None, output_dir: str  = None):
        self.amstrax_dir = amstrax_dir or settings.stbc_amstrax_dir
        self.log_dir = log_dir or settings.stbc_log_dir
        self.output_dir = output_dir or settings.stbc_output_dir
        self._last_submit_by_run = {}  # type: Dict[int, float]
        self._cooldown_seconds = 45

    def submit_run(self, run_id: int, target: Union[str, List[str]] = "events") -> dict:
        now = time.time()
        last = self._last_submit_by_run.get(int(run_id), 0.0)
        targets = target if isinstance(target, list) else [target]
        if now - last < self._cooldown_seconds:
            return {
                "run_id": int(run_id),
                "target": targets,
                "job_name": None,
                "submitted": False,
                "returncode": 409,
                "stdout": "",
                "stderr": "Submission blocked: cooldown active for this run. Wait and refresh status.",
            }

        run_id_s = f"{int(run_id):06d}"
        target_label = "_".join(targets)
        job_name = f"process_{run_id_s}_manual_{target_label}_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"

        cmd = [
            "python",
            "auto_processing.py",
            "--run_id",
            run_id_s,
            "--target",
        ]
        cmd.extend(targets)
        cmd.extend(["--output_folder", self.output_dir, "--production"])
        try:
            os.makedirs(self.log_dir, exist_ok=True)
            p = subprocess.run(cmd, cwd=self.amstrax_dir, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            if p.returncode == 0:
                self._last_submit_by_run[int(run_id)] = now
            return {
                "run_id": int(run_id),
                "target": targets,
                "job_name": job_name,
                "submitted": p.returncode == 0,
                "returncode": p.returncode,
                "stdout": p.stdout[-4000:],
                "stderr": p.stderr[-4000:],
            }
        except Exception as e:
            return {
                "run_id": int(run_id),
                "target": targets,
                "job_name": job_name,
                "submitted": False,
                "returncode": -1,
                "stdout": "",
                "stderr": str(e),
            }
