from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, Optional


class ExportNamingMode(str, Enum):
    KEEP_ORIGINAL = "keep"
    PREFIX = "prefix"
    SUFFIX = "suffix"


class ResizeMode(str, Enum):
    NONE = "none"
    WIDTH = "width"
    HEIGHT = "height"
    PERCENT = "percent"


@dataclass
class ExportSettings:
    output_format: str = "png"  # or "jpeg"
    output_dir: Optional[str] = None
    naming_mode: ExportNamingMode = ExportNamingMode.SUFFIX
    custom_prefix: str = "wm_"
    custom_suffix: str = "_watermarked"
    prevent_overwrite: bool = True
    jpeg_quality: int = 90  # 0-100
    resize_mode: ResizeMode = ResizeMode.NONE
    resize_value: Optional[int] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "output_format": self.output_format,
            "output_dir": self.output_dir,
            "naming_mode": self.naming_mode.value,
            "custom_prefix": self.custom_prefix,
            "custom_suffix": self.custom_suffix,
            "prevent_overwrite": self.prevent_overwrite,
            "jpeg_quality": self.jpeg_quality,
            "resize_mode": self.resize_mode.value,
            "resize_value": self.resize_value,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ExportSettings":
        return cls(
            output_format=data.get("output_format", "png"),
            output_dir=data.get("output_dir"),
            naming_mode=ExportNamingMode(data.get("naming_mode", ExportNamingMode.SUFFIX.value)),
            custom_prefix=data.get("custom_prefix", "wm_"),
            custom_suffix=data.get("custom_suffix", "_watermarked"),
            prevent_overwrite=bool(data.get("prevent_overwrite", True)),
            jpeg_quality=int(data.get("jpeg_quality", 90)),
            resize_mode=ResizeMode(data.get("resize_mode", ResizeMode.NONE.value)),
            resize_value=data.get("resize_value"),
        )

