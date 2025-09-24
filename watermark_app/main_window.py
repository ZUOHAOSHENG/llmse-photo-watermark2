from __future__ import annotations

from pathlib import Path
from typing import List, Optional

from PySide6.QtCore import QPointF, Qt
from PySide6.QtGui import QAction, QCloseEvent, QIcon
from PySide6.QtWidgets import (QFileDialog, QGridLayout, QMainWindow,
                               QMessageBox, QScrollArea, QSplitter,
                               QStatusBar, QToolBar, QWidget)

from .export_settings import ExportNamingMode, ExportSettings, ResizeMode
from .image_manager import ImageManager, ImageItem
from .settings_store import SettingsStore
from .template_manager import TemplateManager
from .utils import anchor_to_position
from .watermark_renderer import WatermarkRenderer
from .watermark_settings import WatermarkAnchor, WatermarkLayout, WatermarkSettings
from .widgets.controls_panel import ControlsPanel
from .widgets.image_list_widget import ImageListWidget
from .widgets.preview_widget import PreviewWidget


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("批量水印工具")
        self.resize(1200, 720)

        self.image_manager = ImageManager()
        self.renderer = WatermarkRenderer()
        self.settings_store = SettingsStore()
        self.template_manager = TemplateManager()
        self.watermark_settings, self.export_settings = self.settings_store.load()

        self._build_ui()
        self._connect_signals()
        self._load_initial_state()

    def _build_ui(self) -> None:
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)

        central = QWidget()
        central_layout = QGridLayout(central)
        central_layout.setContentsMargins(0, 0, 0, 0)

        splitter = QSplitter(Qt.Horizontal)
        central_layout.addWidget(splitter)

        # Left: image list
        self.image_list = ImageListWidget()
        splitter.addWidget(self.image_list)

        # Right: preview and controls
        right_widget = QWidget()
        right_layout = QGridLayout(right_widget)
        right_layout.setContentsMargins(6, 6, 6, 6)
        right_layout.setSpacing(6)

        self.preview = PreviewWidget()
        right_layout.addWidget(self.preview, 0, 0)

        self.controls = ControlsPanel()
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(self.controls)
        right_layout.addWidget(scroll, 1, 0)

        splitter.addWidget(right_widget)
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 2)

        self.setCentralWidget(central)

        # Toolbar
        toolbar = QToolBar("操作")
        toolbar.setMovable(False)
        self.addToolBar(toolbar)

        self.import_images_action = QAction("导入图片", self)
        self.import_folder_action = QAction("导入文件夹", self)
        self.remove_image_action = QAction("移除选中", self)
        self.clear_list_action = QAction("清空列表", self)
        self.export_selected_action = QAction("导出选中", self)
        self.export_all_action = QAction("导出全部", self)

        toolbar.addAction(self.import_images_action)
        toolbar.addAction(self.import_folder_action)
        toolbar.addSeparator()
        toolbar.addAction(self.remove_image_action)
        toolbar.addAction(self.clear_list_action)
        toolbar.addSeparator()
        toolbar.addAction(self.export_selected_action)
        toolbar.addAction(self.export_all_action)

    def _connect_signals(self) -> None:
        self.import_images_action.triggered.connect(self._import_images)
        self.import_folder_action.triggered.connect(self._import_folder)
        self.remove_image_action.triggered.connect(self._remove_selected_image)
        self.clear_list_action.triggered.connect(self._clear_images)
        self.export_selected_action.triggered.connect(self._export_selected)
        self.export_all_action.triggered.connect(self._export_all)

        self.image_list.files_dropped.connect(self._on_files_dropped)
        self.image_list.selection_changed.connect(self._on_image_selected)

        self.controls.watermarkChanged.connect(self._on_watermark_changed)
        self.controls.exportChanged.connect(self._on_export_changed)
        self.controls.anchorSelected.connect(self._on_anchor_selected)
        self.controls.browseWatermarkImageRequested.connect(self._select_watermark_image)
        self.controls.browseOutputDirRequested.connect(self._select_output_directory)
        self.controls.saveTemplateRequested.connect(self._save_template)
        self.controls.loadTemplateRequested.connect(self._load_template)
        self.controls.deleteTemplateRequested.connect(self._delete_template)

        self.preview.positionChanged.connect(self._on_preview_position_changed)
        self.preview.anchorChanged.connect(self._on_preview_anchor_changed)

    def _load_initial_state(self) -> None:
        self.controls.set_settings(self.watermark_settings, self.export_settings)
        templates = self.template_manager.list_templates()
        self.controls.set_templates(templates)

    # Image handling -------------------
    def _add_images(self, paths: List[str]) -> None:
        added_paths = self.image_manager.add_paths(paths)
        for path in added_paths:
            pixmap = self.image_manager.load_thumbnail(path)
            item = next((it for it in self.image_manager.items if it.path == path), None)
            if item:
                self.image_list.add_image_item(item, pixmap)
        if self.image_list.count() and self.image_list.currentRow() < 0:
            self.image_list.setCurrentRow(0)
            self._load_preview_image(0)
        self.status_bar.showMessage(f"已添加 {len(added_paths)} 张图片", 3000)

    def _import_images(self) -> None:
        files, _ = QFileDialog.getOpenFileNames(
            self,
            "选择图片",
            str(Path.home()),
            "图片文件 (*.jpg *.jpeg *.png *.bmp *.tif *.tiff)"
        )
        if files:
            self._add_images(files)

    def _import_folder(self) -> None:
        directory = QFileDialog.getExistingDirectory(self, "选择文件夹", str(Path.home()))
        if directory:
            added = self.image_manager.add_directory(directory)
            self._refresh_image_list()
            self.status_bar.showMessage(f"从文件夹添加 {len(added)} 张图片", 3000)

    def _on_files_dropped(self, files: List[str]) -> None:
        folders = []
        direct_files = []
        for f in files:
            path = Path(f)
            if path.is_dir():
                folders.append(path)
            elif path.is_file():
                direct_files.append(f)
        if direct_files:
            self._add_images(direct_files)
        for folder in folders:
            self.image_manager.add_directory(folder)
        if folders:
            self._refresh_image_list()

    def _refresh_image_list(self) -> None:
        self.image_list.clear()
        for item in self.image_manager.items:
            pixmap = self.image_manager.load_thumbnail(item.path)
            self.image_list.add_image_item(item, pixmap)

    def _on_image_selected(self, index: int) -> None:
        self._load_preview_image(index)

    def _load_preview_image(self, index: int) -> None:
        if index < 0:
            self.preview.set_image(None)
            return
        items = list(self.image_manager.items)
        if index >= len(items):
            return
        item = items[index]
        pixmap = self.image_manager.load_pixmap(item.path)
        if pixmap:
            self.preview.set_image(pixmap)
            self.preview.update_settings(self.watermark_settings)

    def _remove_selected_image(self) -> None:
        if self.image_list.count() == 0:
            return
        row = self.image_list.currentRow()
        if row < 0:
            return
        self.image_manager.remove_index(row)
        self.image_list.takeItem(row)
        next_row = min(row, self.image_list.count() - 1)
        if next_row >= 0:
            self.image_list.setCurrentRow(next_row)
            self._load_preview_image(next_row)
        else:
            self.preview.set_image(None)

    def _clear_images(self) -> None:
        self.image_manager.clear()
        self.image_list.clear()
        self.preview.set_image(None)

    # Watermark changes ---------------
    def _on_watermark_changed(self, settings: WatermarkSettings) -> None:
        self.watermark_settings = settings
        self.preview.update_settings(settings)

    def _on_anchor_selected(self, anchor: WatermarkAnchor) -> None:
        layout = self.watermark_settings.layout
        layout.anchor = anchor
        self.watermark_settings.layout = layout
        self.preview.set_layout(layout)

    def _on_preview_position_changed(self, x: float, y: float) -> None:
        layout = self.watermark_settings.layout
        layout.position = (x, y)
        layout.anchor = WatermarkAnchor.CENTER
        self.watermark_settings.layout = layout
        self.controls.update_layout(layout)
        self.preview.set_layout(layout)

    def _on_preview_anchor_changed(self, anchor: WatermarkAnchor) -> None:
        layout = self.watermark_settings.layout
        layout.anchor = anchor
        self.watermark_settings.layout = layout
        self.controls.update_layout(layout)

    # Export settings -----------------
    def _on_export_changed(self, export: ExportSettings) -> None:
        self.export_settings = export

    def _select_watermark_image(self) -> None:
        file, _ = QFileDialog.getOpenFileName(
            self,
            "选择水印图片",
            str(Path.home()),
            "图片文件 (*.png *.jpg *.jpeg *.bmp *.tif *.tiff)"
        )
        if file:
            self.controls.set_watermark_image_path(file)

    def _select_output_directory(self) -> None:
        directory = QFileDialog.getExistingDirectory(self, "选择输出文件夹", str(Path.home()))
        if directory:
            self.controls.set_output_directory(directory)

    # Templates -----------------------
    def _save_template(self, name: str) -> None:
        self.template_manager.save_template(name, self.watermark_settings, self.export_settings)
        templates = self.template_manager.list_templates()
        self.controls.set_templates(templates)
        self.status_bar.showMessage(f"已保存模板: {name}", 3000)

    def _load_template(self, name: str) -> None:
        try:
            watermark, export = self.template_manager.load_template(name)
        except FileNotFoundError:
            QMessageBox.warning(self, "模板不存在", f"未找到模板 {name}")
            return
        self.watermark_settings = watermark
        self.export_settings = export
        self.controls.set_settings(watermark, export)
        self.preview.update_settings(watermark)
        self.status_bar.showMessage(f"已加载模板: {name}", 3000)

    def _delete_template(self, name: str) -> None:
        self.template_manager.delete_template(name)
        templates = self.template_manager.list_templates()
        self.controls.set_templates(templates)
        self.status_bar.showMessage(f"已删除模板: {name}", 3000)

    # Export --------------------------
    def _export_selected(self) -> None:
        index = self.image_list.currentRow()
        if index < 0:
            QMessageBox.information(self, "提示", "请先选择图片")
            return
        items = list(self.image_manager.items)
        if index >= len(items):
            return
        self._export_images([items[index]])

    def _export_all(self) -> None:
        items = list(self.image_manager.items)
        if not items:
            QMessageBox.information(self, "提示", "没有可导出的图片")
            return
        self._export_images(items)

    def _export_images(self, items: List[ImageItem]) -> None:
        if not self.export_settings.output_dir:
            QMessageBox.warning(self, "缺少输出目录", "请先在右侧设置中选择输出文件夹")
            return
        output_dir = Path(self.export_settings.output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        if self.export_settings.prevent_overwrite:
            for item in items:
                if output_dir.samefile(item.path.parent):
                    QMessageBox.warning(self, "输出目录无效", "默认禁止导出到原图片所在的文件夹，请选择其他文件夹。")
                    return

        success_count = 0
        for item in items:
            result_path = self._determine_output_path(item.path, output_dir)
            if result_path is None:
                continue
            base_image = self.image_manager.load_pixmap(item.path)
            if not base_image:
                continue
            image = base_image.toImage()
            image = self._resize_image(image)
            layout = self.watermark_settings.layout
            position = QPointF(layout.position[0] * image.width(), layout.position[1] * image.height())
            anchor = anchor_to_position(layout.anchor)
            result_image = self.renderer.apply_watermark(
                image,
                self.watermark_settings,
                position,
                QPointF(anchor[0], anchor[1])
            )
            format_name = self.export_settings.output_format.upper()
            if format_name in ("JPG", "JPEG"):
                quality = max(0, min(100, int(self.export_settings.jpeg_quality)))
                result_image.save(str(result_path), format_name, quality)
            else:
                result_image.save(str(result_path), format_name)
            success_count += 1
        self.status_bar.showMessage(f"导出完成，共处理 {success_count} 张图片", 5000)

    def _resize_image(self, image):
        mode = self.export_settings.resize_mode
        value = self.export_settings.resize_value or 0
        if mode == ResizeMode.NONE or value <= 0:
            return image
        width = image.width()
        height = image.height()
        if mode == ResizeMode.WIDTH:
            new_width = value
            new_height = int(height * (new_width / width))
        elif mode == ResizeMode.HEIGHT:
            new_height = value
            new_width = int(width * (new_height / height))
        elif mode == ResizeMode.PERCENT:
            scale = value / 100.0
            new_width = int(width * scale)
            new_height = int(height * scale)
        else:
            return image
        new_width = max(1, new_width)
        new_height = max(1, new_height)
        return image.scaled(new_width, new_height, Qt.KeepAspectRatio, Qt.SmoothTransformation)

    def _determine_output_path(self, source: Path, output_dir: Path) -> Optional[Path]:
        stem = source.stem
        if self.export_settings.naming_mode == ExportNamingMode.PREFIX:
            stem = f"{self.export_settings.custom_prefix}{stem}"
        elif self.export_settings.naming_mode == ExportNamingMode.SUFFIX:
            stem = f"{stem}{self.export_settings.custom_suffix}"
        extension = ".png" if self.export_settings.output_format.lower() == "png" else ".jpg"
        target = output_dir / f"{stem}{extension}"
        counter = 1
        while target.exists():
            target = output_dir / f"{stem}_{counter}{extension}"
            counter += 1
        return target

    def closeEvent(self, event: QCloseEvent) -> None:
        self.settings_store.save(self.watermark_settings, self.export_settings)
        super().closeEvent(event)



