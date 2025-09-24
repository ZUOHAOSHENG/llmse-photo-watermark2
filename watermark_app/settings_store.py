from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Optional

from .export_settings import ExportSettings
from .watermark_settings import WatermarkSettings

DEFAULT_STATE_FILENAME = "app_state.json"
DEFAULT_STORAGE_DIRNAME = ".llmse_watermark"


class SettingsStore:
    def __init__(self, storage_path: Optional[Path] = None) -> None:
        if storage_path is None:
            base_dir = Path.home() / DEFAULT_STORAGE_DIRNAME
            base_dir.mkdir(parents=True, exist_ok=True)
            storage_path = base_dir / DEFAULT_STATE_FILENAME
        else:
            storage_path.parent.mkdir(parents=True, exist_ok=True)
        self.storage_path = storage_path

    def load(self) -> tuple[WatermarkSettings, ExportSettings]:
        if not self.storage_path.exists():
            return WatermarkSettings(), ExportSettings()
        try:
            raw = json.loads(self.storage_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return WatermarkSettings(), ExportSettings()
        watermark_state = raw.get("watermark", {})
        export_state = raw.get("export", {})
        return WatermarkSettings.from_dict(watermark_state), ExportSettings.from_dict(export_state)

    def save(self, watermark: WatermarkSettings, export: ExportSettings) -> None:
        payload: Dict[str, Any] = {
            "watermark": watermark.to_dict(),
            "export": export.to_dict(),
        }
        self.storage_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

