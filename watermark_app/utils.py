from __future__ import annotations

from typing import Tuple

from PySide6.QtGui import QColor

from .watermark_settings import Color, WatermarkAnchor


def clamp(value: float, min_value: float, max_value: float) -> float:
    return max(min_value, min(max_value, value))


def color_to_qcolor(color: Color) -> QColor:
    r, g, b, a = color
    return QColor(r, g, b, a)


def qcolor_to_tuple(color: QColor) -> Color:
    return color.red(), color.green(), color.blue(), color.alpha()


def anchor_to_position(anchor: WatermarkAnchor) -> Tuple[float, float]:
    mapping = {
        WatermarkAnchor.TOP_LEFT: (0.0, 0.0),
        WatermarkAnchor.TOP_CENTER: (0.5, 0.0),
        WatermarkAnchor.TOP_RIGHT: (1.0, 0.0),
        WatermarkAnchor.CENTER_LEFT: (0.0, 0.5),
        WatermarkAnchor.CENTER: (0.5, 0.5),
        WatermarkAnchor.CENTER_RIGHT: (1.0, 0.5),
        WatermarkAnchor.BOTTOM_LEFT: (0.0, 1.0),
        WatermarkAnchor.BOTTOM_CENTER: (0.5, 1.0),
        WatermarkAnchor.BOTTOM_RIGHT: (1.0, 1.0),
    }
    return mapping[anchor]


def nearest_anchor(position: Tuple[float, float]) -> WatermarkAnchor:
    x, y = position
    x_bucket = 0 if x < 0.33 else (1 if x <= 0.66 else 2)
    y_bucket = 0 if y < 0.33 else (1 if y <= 0.66 else 2)
    grid = {
        (0, 0): WatermarkAnchor.TOP_LEFT,
        (1, 0): WatermarkAnchor.TOP_CENTER,
        (2, 0): WatermarkAnchor.TOP_RIGHT,
        (0, 1): WatermarkAnchor.CENTER_LEFT,
        (1, 1): WatermarkAnchor.CENTER,
        (2, 1): WatermarkAnchor.CENTER_RIGHT,
        (0, 2): WatermarkAnchor.BOTTOM_LEFT,
        (1, 2): WatermarkAnchor.BOTTOM_CENTER,
        (2, 2): WatermarkAnchor.BOTTOM_RIGHT,
    }
    return grid[(x_bucket, y_bucket)]

