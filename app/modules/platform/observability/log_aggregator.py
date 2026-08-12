from __future__ import annotations

import json
import time
from datetime import datetime, timezone
from typing import Any

from app.core.logging import get_logger
log = get_logger(__name__)


class LogAggregator:
    async def enrich(
        self,
        log_record: dict,
        trace_id: str = "",
        tenant_id: str = "",
        plant_id: str = "",
        module: str = "",
        model_id: str = ""
    ) -> dict:
        enriched = dict(log_record)
        enriched.update({
            "trace_id": trace_id,
            "tenant_id": tenant_id,
            "plant_id": plant_id,
            "module": module,
            "model_id": model_id,
            "timestamp": enriched.get("timestamp", datetime.now(timezone.utc).isoformat()),
            "environment": "production",
            "service": "abhedya-ai-core"
        })
        return enriched

    async def format_loki(self, log_record: dict) -> dict:
        timestamp_ns = str(time.time_ns())
        service = log_record.get("service", "abhedya-ai-core")
        level = log_record.get("level", "info")
        return {
            "streams": [
                {
                    "stream": {
                        "service": service,
                        "level": level
                    },
                    "values": [
                        [timestamp_ns, json.dumps(log_record)]
                    ]
                }
            ]
        }

    async def aggregate_by_module(self, logs: list[dict], module: str) -> list[dict]:
        return [log_rec for log_rec in logs if log_rec.get("module") == module]

    async def aggregate_error_logs(self, logs: list[dict], window_minutes: int = 60) -> dict:
        error_logs = [l for l in logs if str(l.get("level", "")).lower() in ("error", "critical")]
        total_errors = len(error_logs)
        by_module: dict[str, int] = {}
        by_level: dict[str, int] = {}
        for log_rec in error_logs:
            mod = log_rec.get("module", "unknown")
            lvl = str(log_rec.get("level", "error")).lower()
            by_module[mod] = by_module.get(mod, 0) + 1
            by_level[lvl] = by_level.get(lvl, 0) + 1

        return {
            "total_errors": total_errors,
            "by_module": by_module,
            "by_level": by_level,
            "error_rate": total_errors / len(logs) if logs else 0.0
        }

    async def extract_trace_context(self, log_record: dict) -> dict:
        return {
            "trace_id": log_record.get("trace_id", ""),
            "span_id": log_record.get("span_id", ""),
            "request_id": log_record.get("request_id", "")
        }

    async def create_structured_log(self, level: str, message: str, module: str, **kwargs) -> dict:
        record = {
            "level": level,
            "message": message,
            "module": module,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "service": "abhedya-ai-core"
        }
        record.update(kwargs)
        return await self.format_loki(record)
