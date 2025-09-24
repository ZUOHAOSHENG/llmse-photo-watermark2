from __future__ import annotations

from pathlib import Path
from typing import Iterable, List, Optional

from PySide6.QtCore import QPoint, QSize, Qt, Signal
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import QListWidget, QListWidgetItem

from ..image_manager import ImageItem


class ImageListWidget(QListWidget):
    files_dropped = Signal(list)
    selection_changed = Signal(int)

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setIconSize(QSize(96, 96))
        self.setSelectionMode(QListWidget.SingleSelection)
        self.setAlternatingRowColors(True)
        self.setSpacing(4)
        self.setAcceptDrops(True)
        self.setDragEnabled(False)
        self.currentRowChanged.connect(self.selection_changed)

    def add_image_item(self, image: ImageItem, thumbnail: Optional[QPixmap]) -> None:
        item = QListWidgetItem(image.name)
        item.setData(Qt.UserRole, str(image.path))
        if thumbnail:
            item.setIcon(thumbnail)
        self.addItem(item)

    def populate(self, images: Iterable[tuple[ImageItem, Optional[QPixmap]]]) -> None:
        self.clear()
        for image, thumbnail in images:
            self.add_image_item(image, thumbnail)
        if self.count():
            self.setCurrentRow(0)

    def update_thumbnails(self, path_to_pixmap: dict[Path, QPixmap]) -> None:
        for index in range(self.count()):
            item = self.item(index)
            path = Path(item.data(Qt.UserRole))
            pixmap = path_to_pixmap.get(path)
            if pixmap:
                item.setIcon(pixmap)

    def dragEnterEvent(self, event) -> None:
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            event.ignore()

    def dragMoveEvent(self, event) -> None:
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            event.ignore()

    def dropEvent(self, event) -> None:
        urls = event.mimeData().urls()
        if not urls:
            return
        files: List[str] = []
        for url in urls:
            local = url.toLocalFile()
            if local:
                files.append(local)
        if files:
            self.files_dropped.emit(files)
        event.acceptProposedAction()

    def remove_selected(self) -> Optional[str]:
        current = self.currentItem()
        if not current:
            return None
        row = self.currentRow()
        path = current.data(Qt.UserRole)
        self.takeItem(row)
        return path

