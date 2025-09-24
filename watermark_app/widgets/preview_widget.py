from __future__ import annotations

from typing import Optional

from PySide6.QtCore import QPointF, QRectF, Qt, Signal
from PySide6.QtGui import QMouseEvent, QPainter, QPixmap
from PySide6.QtWidgets import QWidget

from ..utils import anchor_to_position, clamp
from ..watermark_renderer import WatermarkRenderer
from ..watermark_settings import WatermarkAnchor, WatermarkLayout, WatermarkSettings


class PreviewWidget(QWidget):
    positionChanged = Signal(float, float)
    anchorChanged = Signal(object)

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setMinimumSize(480, 360)
        self._renderer = WatermarkRenderer()
        self._base_pixmap: Optional[QPixmap] = None
        self._scaled_pixmap: Optional[QPixmap] = None
        self._watermark_pixmap: Optional[QPixmap] = None
        self._settings = WatermarkSettings()
        self._layout = WatermarkLayout()
        self._scale_factor = 1.0
        self._draw_rect = QRectF()
        self._dragging = False
        self._drag_delta = QPointF()

    def set_image(self, pixmap: Optional[QPixmap]) -> None:
        self._base_pixmap = pixmap
        self._update_scaled_pixmap()
        self._regenerate_watermark()
        self.update()

    def set_settings(self, settings: WatermarkSettings) -> None:
        self._settings = settings
        self._layout = settings.layout
        self._regenerate_watermark()
        self.update()

    def update_settings(self, settings: WatermarkSettings) -> None:
        self.set_settings(settings)

    def _regenerate_watermark(self) -> None:
        if not self._base_pixmap:
            self._watermark_pixmap = None
            return
        render_result = self._renderer.build_watermark(self._base_pixmap.size(), self._settings)
        self._watermark_pixmap = render_result.pixmap

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        self._update_scaled_pixmap()

    def _update_scaled_pixmap(self) -> None:
        if not self._base_pixmap:
            self._scaled_pixmap = None
            self._scale_factor = 1.0
            self._draw_rect = QRectF()
            return
        target_width = max(1, self.width())
        target_height = max(1, self.height())
        base_width = self._base_pixmap.width()
        base_height = self._base_pixmap.height()
        if base_width == 0 or base_height == 0:
            return
        scale = min(target_width / base_width, target_height / base_height)
        self._scale_factor = scale
        scaled_width = max(1, int(base_width * scale))
        scaled_height = max(1, int(base_height * scale))
        self._scaled_pixmap = self._base_pixmap.scaled(scaled_width, scaled_height, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        offset_x = (target_width - self._scaled_pixmap.width()) / 2
        offset_y = (target_height - self._scaled_pixmap.height()) / 2
        self._draw_rect = QRectF(offset_x, offset_y, self._scaled_pixmap.width(), self._scaled_pixmap.height())

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.fillRect(self.rect(), Qt.black)
        if not self._base_pixmap or not self._scaled_pixmap:
            painter.end()
            return
        painter.drawPixmap(self._draw_rect.topLeft(), self._scaled_pixmap)
        if self._watermark_pixmap:
            self._draw_watermark(painter)
        painter.end()

    def _draw_watermark(self, painter: QPainter) -> None:
        if not self._base_pixmap or not self._watermark_pixmap:
            return
        anchor_ratio = anchor_to_position(self._layout.anchor)
        base_width = self._base_pixmap.width()
        base_height = self._base_pixmap.height()
        pos_x = self._layout.position[0] * base_width
        pos_y = self._layout.position[1] * base_height
        wm_width = self._watermark_pixmap.width()
        wm_height = self._watermark_pixmap.height()
        top_left_x = pos_x - (anchor_ratio[0] * wm_width)
        top_left_y = pos_y - (anchor_ratio[1] * wm_height)
        draw_x = self._draw_rect.x() + top_left_x * self._scale_factor
        draw_y = self._draw_rect.y() + top_left_y * self._scale_factor
        scaled_width = max(1, int(wm_width * self._scale_factor))
        scaled_height = max(1, int(wm_height * self._scale_factor))
        scaled_pixmap = self._watermark_pixmap.scaled(scaled_width, scaled_height, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        painter.drawPixmap(draw_x, draw_y, scaled_pixmap)

    def _watermark_rect_base(self) -> Optional[QRectF]:
        if not self._base_pixmap or not self._watermark_pixmap:
            return None
        anchor_ratio = anchor_to_position(self._layout.anchor)
        base_width = self._base_pixmap.width()
        base_height = self._base_pixmap.height()
        pos_x = self._layout.position[0] * base_width
        pos_y = self._layout.position[1] * base_height
        wm_width = self._watermark_pixmap.width()
        wm_height = self._watermark_pixmap.height()
        top_left_x = pos_x - (anchor_ratio[0] * wm_width)
        top_left_y = pos_y - (anchor_ratio[1] * wm_height)
        return QRectF(top_left_x, top_left_y, wm_width, wm_height)

    def _watermark_rect_widget(self) -> Optional[QRectF]:
        base_rect = self._watermark_rect_base()
        if base_rect is None:
            return None
        draw_x = self._draw_rect.x() + base_rect.x() * self._scale_factor
        draw_y = self._draw_rect.y() + base_rect.y() * self._scale_factor
        width = base_rect.width() * self._scale_factor
        height = base_rect.height() * self._scale_factor
        return QRectF(draw_x, draw_y, width, height)

    def _widget_to_base(self, point: QPointF) -> QPointF:
        relative = point - self._draw_rect.topLeft()
        base_x = relative.x() / self._scale_factor
        base_y = relative.y() / self._scale_factor
        return QPointF(base_x, base_y)

    def mousePressEvent(self, event: QMouseEvent) -> None:
        if event.button() != Qt.LeftButton:
            super().mousePressEvent(event)
            return
        rect = self._watermark_rect_widget()
        if rect and rect.contains(event.position()):
            self._dragging = True
            base_rect = self._watermark_rect_base()
            if base_rect:
                pointer_base = self._widget_to_base(event.position())
                center = base_rect.center()
                self._drag_delta = pointer_base - center
            event.accept()
        else:
            super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        if not self._dragging or not self._base_pixmap or not self._watermark_pixmap:
            super().mouseMoveEvent(event)
            return
        base_rect = self._watermark_rect_base()
        if not base_rect:
            return
        pointer_base = self._widget_to_base(event.position())
        new_center_x = pointer_base.x() - self._drag_delta.x()
        new_center_y = pointer_base.y() - self._drag_delta.y()
        half_w = base_rect.width() / 2
        half_h = base_rect.height() / 2
        base_width = self._base_pixmap.width()
        base_height = self._base_pixmap.height()
        new_center_x = clamp(new_center_x, half_w, base_width - half_w)
        new_center_y = clamp(new_center_y, half_h, base_height - half_h)
        normalized_x = new_center_x / base_width
        normalized_y = new_center_y / base_height
        self.positionChanged.emit(normalized_x, normalized_y)
        self.anchorChanged.emit(WatermarkAnchor.CENTER)
        event.accept()

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.LeftButton and self._dragging:
            self._dragging = False
            event.accept()
        else:
            super().mouseReleaseEvent(event)

    def set_layout(self, layout: WatermarkLayout) -> None:
        self._layout = layout
        self.update()

    def current_layout(self) -> WatermarkLayout:
        return self._layout

