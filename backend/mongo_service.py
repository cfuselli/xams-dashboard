from __future__ import annotations

from typing import Any

from pymongo import MongoClient

from .config import settings
from .models import DataEntry, RunDetails, RunSummary


class MongoService:
    def __init__(self, mongo_uri: str | None = None):
        self.client = MongoClient(mongo_uri or settings.mongo_uri)
        self.runs = self.client[settings.run_db][settings.run_collection]
        self.processing = self.client[settings.processing_db][settings.processing_collection]

    @staticmethod
    def _normalize_data_entry(entry: dict[str, Any]) -> DataEntry:
        return DataEntry(
            data_type=entry.get("type", "unknown"),
            host=entry.get("host"),
            location=entry.get("location"),
            lineage_hash=entry.get("lineage_hash") or entry.get("lineage") or entry.get("hash"),
            amstrax_version=entry.get("amstrax_version"),
            raw=entry,
        )

    def get_runs(self, page: int = 1, page_size: int = 25, status: str | None = None) -> list[RunSummary]:
        page = max(1, page)
        query: dict[str, Any] = {}
        if status:
            query["processing_status.status"] = status

        cursor = (
            self.runs.find(query, {"number": 1, "mode": 1, "start": 1, "end": 1, "processing_status": 1, "_id": 0})
            .sort("number", -1)
            .skip((page - 1) * page_size)
            .limit(page_size)
        )
        out: list[RunSummary] = []
        for doc in cursor:
            ps = doc.get("processing_status") or {}
            out.append(
                RunSummary(
                    number=int(doc["number"]),
                    mode=doc.get("mode"),
                    start=doc.get("start"),
                    end=doc.get("end"),
                    processing_status=ps.get("status"),
                )
            )
        return out

    def get_run_doc(self, run_id: int) -> dict[str, Any] | None:
        return self.runs.find_one({"number": int(run_id)}, {"_id": 0})

    def get_run_details(self, run_id: int) -> RunDetails | None:
        doc = self.get_run_doc(run_id)
        if not doc:
            return None

        entries = [self._normalize_data_entry(d) for d in doc.get("data", [])]
        return RunDetails(
            number=int(doc["number"]),
            mode=doc.get("mode"),
            start=doc.get("start"),
            end=doc.get("end"),
            tags=doc.get("tags", []),
            comments=doc.get("comments", []),
            processing_status=doc.get("processing_status"),
            data_entries=entries,
            raw_doc=doc,
        )

    def get_job_status(self, run_id: int) -> dict[str, Any]:
        doc = self.get_run_doc(run_id)
        if not doc:
            return {"found": False, "status": "missing_run"}
        ps = doc.get("processing_status") or {}
        return {
            "found": True,
            "run_id": run_id,
            "status": ps.get("status", "unknown"),
            "time": ps.get("time"),
            "host": ps.get("host"),
            "reason": ps.get("reason"),
        }
