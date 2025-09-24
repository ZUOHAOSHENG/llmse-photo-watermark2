from __future__ import annotations

import json
import re
from pathlib import Path
from typing import List, Optional

from .export_settings import ExportSettings
from .watermark_settings import WatermarkSettings

DEFAULT_TEMPLATE_DIRNAME = "templates"
TEMPLATE_SUFFIX = ".json"
INVALID_CHARS_RE = re.compile(r"[^A-Za-z0-9_-]+")


class TemplateManager:
    def __init__(self, templates_dir: Optional[Path] = None) -> None:
        if templates_dir is None:
            templates_dir = Path.home() / ".llmse_watermark" / DEFAULT_TEMPLATE_DIRNAME
        templates_dir.mkdir(parents=True, exist_ok=True)
        self.templates_dir = templates_dir

    def _sanitize_name(self, name: str) -> str:
        cleaned = name.strip()
        if not cleaned:
            raise ValueError("Template name cannot be empty")
        cleaned = INVALID_CHARS_RE.sub("_", cleaned)
        return cleaned

    def _template_path(self, name: str) -> Path:
        sanitized = self._sanitize_name(name)
        return self.templates_dir / f"{sanitized}{TEMPLATE_SUFFIX}"

    def save_template(self, name: str, watermark: WatermarkSettings, export: ExportSettings) -> Path:
        path = self._template_path(name)
        payload = {
            "name": name,
            "watermark": watermark.to_dict(),
            "export": export.to_dict(),
        }
        path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        return path

    def load_template(self, name: str) -> tuple[WatermarkSettings, ExportSettings]:
        path = self._template_path(name)
        if not path.exists():
            raise FileNotFoundError(f"Template '{name}' does not exist")
        raw = json.loads(path.read_text(encoding="utf-8"))
        watermark_state = raw.get("watermark", {})
        export_state = raw.get("export", {})
        return WatermarkSettings.from_dict(watermark_state), ExportSettings.from_dict(export_state)

    def delete_template(self, name: str) -> None:
        path = self._template_path(name)
        if path.exists():
            path.unlink()

    def list_templates(self) -> List[str]:
        templates: List[str] = []
        for file in sorted(self.templates_dir.glob(f"*{TEMPLATE_SUFFIX}")):
            templates.append(file.stem)
        return templates

