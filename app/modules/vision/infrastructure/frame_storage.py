"""
vision/infrastructure/frame_storage.py — Frame Storage Service.

Saves and retrieves raw frame image bytes.
Storage backend: local disk (default) or S3-compatible (config-driven).

Local disk:
  - Base path: ./storage/frames/{camera_id}/{date}/
  - Filename: {frame_id}.{format}
  - Auto-creates directories
  - Returns relative path string

S3 (future):
  - Controlled by FRAME_STORAGE_BACKEND env var = 's3'
  - Requires FRAME_STORAGE_BUCKET env var
  - Graceful fallback to local if boto3 unavailable
"""
from __future__ import annotations
import os
import asyncio
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from app.core.logging import get_logger

log = get_logger("vision.infrastructure.frame_storage")

DEFAULT_STORAGE_BASE = Path("./storage/frames")

class FrameStorageService:
    def __init__(self, base_path: Path = DEFAULT_STORAGE_BASE):
        self.base_path = base_path

    async def save_frame(self, frame_id: str, camera_id: str, image_bytes: bytes, fmt: str = 'jpeg') -> str:
        date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        dir_path = self.base_path / camera_id / date_str
        dir_path.mkdir(parents=True, exist_ok=True)
        
        filename = f"{frame_id}.{fmt}"
        file_path = dir_path / filename
        
        # async file write
        loop = asyncio.get_running_loop()
        await loop.run_in_executor(None, self._write_file, file_path, image_bytes)
        
        rel_path = f"{camera_id}/{date_str}/{filename}"
        return rel_path

    def _write_file(self, path: Path, data: bytes):
        with open(path, 'wb') as f:
            f.write(data)

    async def get_frame(self, storage_path: str) -> bytes | None:
        file_path = self.base_path / storage_path
        if not file_path.exists():
            return None
        
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, self._read_file, file_path)

    def _read_file(self, path: Path) -> bytes:
        with open(path, 'rb') as f:
            return f.read()

    async def delete_frame(self, storage_path: str) -> bool:
        file_path = self.base_path / storage_path
        if not file_path.exists():
            return False
            
        loop = asyncio.get_running_loop()
        await loop.run_in_executor(None, file_path.unlink)
        return True

    async def get_frame_url(self, storage_path: str) -> str:
        # local return
        return f"/frames/{storage_path}"

    def get_storage_stats(self) -> dict:
        return {
            "backend": "local",
            "base_path": str(self.base_path),
            "exists": self.base_path.exists()
        }
