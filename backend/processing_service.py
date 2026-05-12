from __future__ import annotations

import os
import subprocess
from datetime import datetime

from .config import settings


class ProcessingService:
    def __init__(self, amstrax_dir: str  = None, log_dir: str  = None, output_dir: str  = None):
        self.amstrax_dir = amstrax_dir or settings.stbc_amstrax_dir
        self.log_dir = log_dir or settings.stbc_log_dir
        self.output_dir = output_dir or settings.stbc_output_dir

    def submit_run(self, run_id: int, target: str = "events") -> dict:
        run_id_s = f"{int(run_id):06d}"
        job_name = f"process_{run_id_s}_manual_{target}_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"

        cmd = [
            "python",
            "auto_processing.py",
            "--run_id",
            run_id_s,
            "--target",
            target,
            "--output_folder",
            self.output_dir,
            "--production",
        ]
        try:
            os.makedirs(self.log_dir, exist_ok=True)
            p = subprocess.run(cmd, cwd=self.amstrax_dir, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            return {
                "run_id": int(run_id),
                "target": target,
                "job_name": job_name,
                "submitted": p.returncode == 0,
                "returncode": p.returncode,
                "stdout": p.stdout[-4000:],
                "stderr": p.stderr[-4000:],
            }
        except Exception as e:
            return {
                "run_id": int(run_id),
                "target": target,
                "job_name": job_name,
                "submitted": False,
                "returncode": -1,
                "stdout": "",
                "stderr": str(e),
            }
