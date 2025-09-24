from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import math

from PySide6.QtCore import QPointF, QSize, Qt
from PySide6.QtGui import (QColor, QFont, QFontMetricsF, QImage, QPainter,
                           QPainterPath, QPen, QPixmap, QTransform)

from .image_manager import SUPPORTED_INPUT_EXTENSIONS
from .watermark_settings import (ImageWatermarkSettings, TextWatermarkSettings,
                                 WatermarkSettings, WatermarkType)

TEXT_MARGIN = 16


@dataclass
class WatermarkRenderResult:
    pixmap: Optional[QPixmap]
    size: QSize


class WatermarkRenderer:
    def build_watermark(self, base_size: QSize, settings: WatermarkSettings) -> WatermarkRenderResult:
        if settings.watermark_type == WatermarkType.TEXT:
            pixmap = self._build_text_watermark(base_size, settings.text_settings, settings.rotation)
        else:
            pixmap = self._build_image_watermark(base_size, settings.image_settings, settings.rotation)
        if pixmap is None:
            return WatermarkRenderResult(pixmap=None, size=QSize())
        return WatermarkRenderResult(pixmap=pixmap, size=pixmap.size())

    def _build_text_watermark(self, base_size: QSize, settings: TextWatermarkSettings, rotation: float) -> Optional[QPixmap]:
        if not settings.text.strip():
            return None
        font = QFont(settings.font_family, settings.font_size)
        font.setBold(settings.bold)
        font.setItalic(settings.italic)
        metrics = QFontMetricsF(font)
        text_rect = metrics.tightBoundingRect(settings.text)
        width = max(math.ceil(text_rect.width()) + TEXT_MARGIN * 2, 10)
        height = max(math.ceil(metrics.ascent() + metrics.descent()) + TEXT_MARGIN * 2, 10)
        image = QImage(width, height, QImage.Format_ARGB32_Premultiplied)
        image.fill(Qt.transparent)
        painter = QPainter(image)
        painter.setRenderHint(QPainter.Antialiasing, True)
        painter.setRenderHint(QPainter.TextAntialiasing, True)
        painter.setFont(font)
        path = QPainterPath()
        baseline = TEXT_MARGIN + metrics.ascent()
        start_point = QPointF(TEXT_MARGIN - text_rect.left(), baseline)
        path.addText(start_point, font, settings.text)
        painter.setOpacity(settings.opacity / 100.0)
        if settings.shadow_enabled:
            shadow_color = QColor(0, 0, 0, int(255 * 0.4))
            painter.save()
            painter.translate(settings.shadow_offset[0], settings.shadow_offset[1])
            painter.fillPath(path, shadow_color)
            painter.restore()
        painter.setBrush(QColor(*settings.color))
        painter.setPen(Qt.NoPen)
        painter.fillPath(path, painter.brush())
        if settings.outline_enabled:
            pen = QPen(QColor(0, 0, 0, settings.color[3]))
            pen.setWidth(max(1, settings.outline_width))
            pen.setJoinStyle(Qt.RoundJoin)
            painter.strokePath(path, pen)
        painter.end()
        pixmap = QPixmap.fromImage(image)
        if rotation:
            transform = QTransform()
            transform.rotate(rotation)
            pixmap = pixmap.transformed(transform, Qt.SmoothTransformation)
        return pixmap

    def _build_image_watermark(self, base_size: QSize, settings: ImageWatermarkSettings, rotation: float) -> Optional[QPixmap]:
        if not settings.image_path:
            return None
        path = Path(settings.image_path)
        if not path.exists():
            return None
        pixmap = QPixmap(str(path))
        if pixmap.isNull():
            return None
        target_width = max(1, int(base_size.width() * settings.scale))
        scaled = pixmap.scaledToWidth(target_width, Qt.SmoothTransformation)
        if rotation:
            transform = QTransform()
            transform.rotate(rotation)
            scaled = scaled.transformed(transform, Qt.SmoothTransformation)
        if settings.opacity < 100:
            image = scaled.toImage()
            painter = QPainter(image)
            painter.setCompositionMode(QPainter.CompositionMode_DestinationIn)
            painter.fillRect(image.rect(), QColor(0, 0, 0, int(255 * (settings.opacity / 100.0))))
            painter.end()
            scaled = QPixmap.fromImage(image)
        return scaled

    def apply_watermark(self, base_image: QImage, settings: WatermarkSettings, position: QPointF, anchor_ratio: QPointF) -> QImage:
        result = QImage(base_image)
        painter = QPainter(result)
        painter.setRenderHint(QPainter.Antialiasing, True)
        render_result = self.build_watermark(base_image.size(), settings)
        if not render_result.pixmap:
            painter.end()
            return result
        watermark = render_result.pixmap
        offset_x = watermark.width() * anchor_ratio.x()
        offset_y = watermark.height() * anchor_ratio.y()
        draw_point = QPointF(position.x() - offset_x, position.y() - offset_y)
        painter.drawPixmap(draw_point, watermark)
        painter.end()
        return result



