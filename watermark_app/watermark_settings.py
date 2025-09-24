from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any, Dict, Optional, Tuple

Color = Tuple[int, int, int, int]


class WatermarkType(str, Enum):
    TEXT = "text"
    IMAGE = "image"


class WatermarkAnchor(str, Enum):
    TOP_LEFT = "top_left"
    TOP_CENTER = "top_center"
    TOP_RIGHT = "top_right"
    CENTER_LEFT = "center_left"
    CENTER = "center"
    CENTER_RIGHT = "center_right"
    BOTTOM_LEFT = "bottom_left"
    BOTTOM_CENTER = "bottom_center"
    BOTTOM_RIGHT = "bottom_right"


@dataclass
class TextWatermarkSettings:
    text: str = "Watermark"
    font_family: str = "Arial"
    font_size: int = 32
    bold: bool = False
    italic: bool = False
    color: Color = (255, 255, 255, 255)
    opacity: int = 80  # 0-100
    shadow_enabled: bool = False
    outline_enabled: bool = False
    outline_width: int = 2
    shadow_offset: Tuple[int, int] = (2, 2)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TextWatermarkSettings":
        return cls(**data)


@dataclass
class ImageWatermarkSettings:
    image_path: Optional[str] = None
    scale: float = 0.25
    opacity: int = 70

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ImageWatermarkSettings":
        return cls(**data)


@dataclass
class WatermarkLayout:
    position: Tuple[float, float] = (0.5, 0.5)  # normalized coordinates
    anchor: WatermarkAnchor = WatermarkAnchor.CENTER

    def to_dict(self) -> Dict[str, Any]:
        return {"position": list(self.position), "anchor": self.anchor.value}

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "WatermarkLayout":
        position_data = data.get("position", (0.5, 0.5))
        if isinstance(position_data, list):
            position = (float(position_data[0]), float(position_data[1]))
        else:
            position = position_data
        anchor_value = data.get("anchor", WatermarkAnchor.CENTER.value)
        return cls(position=position, anchor=WatermarkAnchor(anchor_value))


@dataclass
class WatermarkSettings:
    watermark_type: WatermarkType = WatermarkType.TEXT
    text_settings: TextWatermarkSettings = field(default_factory=TextWatermarkSettings)
    image_settings: ImageWatermarkSettings = field(default_factory=ImageWatermarkSettings)
    rotation: float = 0.0
    layout: WatermarkLayout = field(default_factory=WatermarkLayout)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "watermark_type": self.watermark_type.value,
            "text_settings": self.text_settings.to_dict(),
            "image_settings": self.image_settings.to_dict(),
            "rotation": self.rotation,
            "layout": self.layout.to_dict(),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "WatermarkSettings":
        return cls(
            watermark_type=WatermarkType(data.get("watermark_type", WatermarkType.TEXT.value)),
            text_settings=TextWatermarkSettings.from_dict(data.get("text_settings", {})),
            image_settings=ImageWatermarkSettings.from_dict(data.get("image_settings", {})),
            rotation=float(data.get("rotation", 0.0)),
            layout=WatermarkLayout.from_dict(data.get("layout", {})),
        )

