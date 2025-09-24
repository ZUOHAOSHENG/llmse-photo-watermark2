from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence

from PIL import Image
from PySide6.QtCore import Qt
from PySide6.QtGui import QImageReader, QPixmap

SUPPORTED_INPUT_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".tif", ".tiff"}


@dataclass
class ImageItem:
    path: Path

    @property
    def name(self) -> str:
        return self.path.name


class ImageManager:
    def __init__(self) -> None:
        self._items: List[ImageItem] = []
        self._thumbnail_cache: Dict[Path, QPixmap] = {}

    @property
    def items(self) -> Sequence[ImageItem]:
        return list(self._items)

    def clear(self) -> None:
        self._items.clear()
        self._thumbnail_cache.clear()

    def add_paths(self, paths: Iterable[str | Path]) -> List[Path]:
        added: List[Path] = []
        for raw_path in paths:
            path = Path(raw_path)
            if not path.exists() or not path.is_file():
                continue
            if path.suffix.lower() not in SUPPORTED_INPUT_EXTENSIONS:
                continue
            if any(item.path == path for item in self._items):
                continue
            self._items.append(ImageItem(path=path))
            added.append(path)
        return added

    def add_directory(self, directory: str | Path, recursive: bool = True) -> List[Path]:
        dir_path = Path(directory)
        if not dir_path.exists() or not dir_path.is_dir():
            return []
        iterator = dir_path.rglob("*") if recursive else dir_path.glob("*")
        found: List[Path] = []
        for file_path in iterator:
            if file_path.is_file() and file_path.suffix.lower() in SUPPORTED_INPUT_EXTENSIONS:
                found.extend(self.add_paths([file_path]))
        return found

    def remove_index(self, index: int) -> None:
        item = self._items.pop(index)
        self._thumbnail_cache.pop(item.path, None)

    def load_thumbnail(self, path: Path, max_size: int = 96) -> Optional[QPixmap]:
        if path in self._thumbnail_cache:
            return self._thumbnail_cache[path]
        reader = QImageReader(str(path))
        reader.setAutoTransform(True)
        image = reader.read()
        if image.isNull():
            return None
        pixmap = QPixmap.fromImage(image)
        if pixmap.isNull():
            return None
        pixmap = pixmap.scaled(max_size, max_size, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        self._thumbnail_cache[path] = pixmap
        return pixmap

    def load_pixmap(self, path: Path) -> Optional[QPixmap]:
        reader = QImageReader(str(path))
        reader.setAutoTransform(True)
        image = reader.read()
        if image.isNull():
            return None
        return QPixmap.fromImage(image)

    def load_image(self, path: Path) -> Image.Image:
        with Image.open(path) as img:
            return img.convert("RGBA")

