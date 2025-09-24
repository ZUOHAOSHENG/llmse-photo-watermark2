from __future__ import annotations

from dataclasses import replace
from typing import List, Optional

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor, QFontDatabase
from PySide6.QtWidgets import (QButtonGroup, QCheckBox, QComboBox, QDialog, QColorDialog,
                               QFormLayout, QGroupBox, QHBoxLayout, QLabel,
                               QLineEdit, QPushButton, QRadioButton, QSlider,
                               QSpinBox, QStackedWidget, QVBoxLayout, QWidget)

from ..export_settings import ExportNamingMode, ExportSettings, ResizeMode
from ..utils import color_to_qcolor, qcolor_to_tuple
from ..watermark_settings import (ImageWatermarkSettings, TextWatermarkSettings,
                                  WatermarkAnchor, WatermarkSettings,
                                  WatermarkType)


class ControlsPanel(QWidget):
    watermarkChanged = Signal(WatermarkSettings)
    exportChanged = Signal(ExportSettings)
    anchorSelected = Signal(object)
    browseWatermarkImageRequested = Signal()
    browseOutputDirRequested = Signal()
    saveTemplateRequested = Signal(str)
    loadTemplateRequested = Signal(str)
    deleteTemplateRequested = Signal(str)

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._watermark_settings = WatermarkSettings()
        self._export_settings = ExportSettings()
        self._font_db = QFontDatabase()
        self._template_names: List[str] = []
        self._build_ui()
        self._apply_settings_to_ui()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(12)
        layout.addWidget(self._build_watermark_group())
        layout.addWidget(self._build_layout_group())
        layout.addWidget(self._build_export_group())
        layout.addWidget(self._build_template_group())
        layout.addStretch()

    # Watermark group ------------------
    def _build_watermark_group(self) -> QWidget:
        group = QGroupBox("水印设置")
        main_layout = QVBoxLayout(group)

        type_layout = QHBoxLayout()
        self.text_radio = QRadioButton("文本水印")
        self.image_radio = QRadioButton("图片水印")
        self.text_radio.setChecked(True)
        type_layout.addWidget(self.text_radio)
        type_layout.addWidget(self.image_radio)
        type_layout.addStretch()
        main_layout.addLayout(type_layout)

        self.watermark_type_group = QButtonGroup(self)
        self.watermark_type_group.addButton(self.text_radio, id=0)
        self.watermark_type_group.addButton(self.image_radio, id=1)

        self.watermark_stack = QStackedWidget()
        self.watermark_stack.addWidget(self._build_text_panel())
        self.watermark_stack.addWidget(self._build_image_panel())
        main_layout.addWidget(self.watermark_stack)

        rotation_layout = QHBoxLayout()
        rotation_label = QLabel("旋转角度")
        self.rotation_slider = QSlider(Qt.Horizontal)
        self.rotation_slider.setRange(-180, 180)
        self.rotation_slider.setValue(0)
        self.rotation_spin = QSpinBox()
        self.rotation_spin.setRange(-180, 180)
        self.rotation_spin.setValue(0)
        rotation_layout.addWidget(rotation_label)
        rotation_layout.addWidget(self.rotation_slider)
        rotation_layout.addWidget(self.rotation_spin)
        main_layout.addLayout(rotation_layout)

        self.rotation_slider.valueChanged.connect(self.rotation_spin.setValue)
        self.rotation_spin.valueChanged.connect(self.rotation_slider.setValue)
        self.rotation_slider.valueChanged.connect(self._on_rotation_changed)

        self.watermark_type_group.idToggled.connect(self._on_watermark_type_changed)

        return group

    def _build_text_panel(self) -> QWidget:
        widget = QWidget()
        layout = QFormLayout(widget)
        layout.setLabelAlignment(Qt.AlignLeft)

        self.text_input = QLineEdit()
        layout.addRow("内容", self.text_input)

        self.font_combo = QComboBox()
        self.font_combo.addItems(self._font_db.families())
        layout.addRow("字体", self.font_combo)

        self.font_size_spin = QSpinBox()
        self.font_size_spin.setRange(6, 200)
        self.font_size_spin.setValue(32)
        layout.addRow("字号", self.font_size_spin)

        style_layout = QHBoxLayout()
        self.bold_check = QCheckBox("粗体")
        self.italic_check = QCheckBox("斜体")
        style_layout.addWidget(self.bold_check)
        style_layout.addWidget(self.italic_check)
        style_layout.addStretch()
        layout.addRow("样式", style_layout)

        color_layout = QHBoxLayout()
        self.color_preview = QLabel()
        self.color_preview.setFixedSize(32, 20)
        self.color_preview.setAutoFillBackground(True)
        self.color_button = QPushButton("选择颜色")
        color_layout.addWidget(self.color_preview)
        color_layout.addWidget(self.color_button)
        color_layout.addStretch()
        layout.addRow("颜色", color_layout)

        self.opacity_slider = QSlider(Qt.Horizontal)
        self.opacity_slider.setRange(0, 100)
        self.opacity_slider.setValue(80)
        layout.addRow("透明度", self.opacity_slider)

        self.shadow_check = QCheckBox("启用阴影")
        layout.addRow("阴影", self.shadow_check)

        outline_layout = QHBoxLayout()
        self.outline_check = QCheckBox("启用描边")
        self.outline_width_spin = QSpinBox()
        self.outline_width_spin.setRange(1, 10)
        self.outline_width_spin.setValue(2)
        outline_layout.addWidget(self.outline_check)
        outline_layout.addWidget(QLabel("宽度"))
        outline_layout.addWidget(self.outline_width_spin)
        outline_layout.addStretch()
        layout.addRow("描边", outline_layout)

        self.text_input.textChanged.connect(self._on_text_settings_changed)
        self.font_combo.currentTextChanged.connect(self._on_text_settings_changed)
        self.font_size_spin.valueChanged.connect(self._on_text_settings_changed)
        self.bold_check.toggled.connect(self._on_text_settings_changed)
        self.italic_check.toggled.connect(self._on_text_settings_changed)
        self.color_button.clicked.connect(self._on_color_clicked)
        self.opacity_slider.valueChanged.connect(self._on_text_settings_changed)
        self.shadow_check.toggled.connect(self._on_text_settings_changed)
        self.outline_check.toggled.connect(self._on_text_settings_changed)
        self.outline_width_spin.valueChanged.connect(self._on_text_settings_changed)

        return widget

    def _build_image_panel(self) -> QWidget:
        widget = QWidget()
        layout = QFormLayout(widget)
        layout.setLabelAlignment(Qt.AlignLeft)

        path_layout = QHBoxLayout()
        self.image_path_edit = QLineEdit()
        browse_button = QPushButton("浏览…")
        path_layout.addWidget(self.image_path_edit)
        path_layout.addWidget(browse_button)
        layout.addRow("水印图片", path_layout)

        self.image_scale_slider = QSlider(Qt.Horizontal)
        self.image_scale_slider.setRange(5, 100)
        self.image_scale_slider.setValue(25)
        layout.addRow("缩放(%)", self.image_scale_slider)

        self.image_opacity_slider = QSlider(Qt.Horizontal)
        self.image_opacity_slider.setRange(0, 100)
        self.image_opacity_slider.setValue(70)
        layout.addRow("透明度", self.image_opacity_slider)

        browse_button.clicked.connect(self.browseWatermarkImageRequested.emit)
        self.image_path_edit.textChanged.connect(self._on_image_settings_changed)
        self.image_scale_slider.valueChanged.connect(self._on_image_settings_changed)
        self.image_opacity_slider.valueChanged.connect(self._on_image_settings_changed)

        return widget

    # Layout group ------------------
    def _build_layout_group(self) -> QWidget:
        group = QGroupBox("位置与布局")
        layout = QVBoxLayout(group)

        self.anchor_buttons: dict[WatermarkAnchor, QPushButton] = {}
        grid_layout = QVBoxLayout()
        anchors = [
            [WatermarkAnchor.TOP_LEFT, WatermarkAnchor.TOP_CENTER, WatermarkAnchor.TOP_RIGHT],
            [WatermarkAnchor.CENTER_LEFT, WatermarkAnchor.CENTER, WatermarkAnchor.CENTER_RIGHT],
            [WatermarkAnchor.BOTTOM_LEFT, WatermarkAnchor.BOTTOM_CENTER, WatermarkAnchor.BOTTOM_RIGHT],
        ]
        for row in anchors:
            row_layout = QHBoxLayout()
            for anchor in row:
                button = QPushButton(anchor.name.replace("_", " "))
                button.setCheckable(True)
                button.clicked.connect(lambda checked, a=anchor: self._on_anchor_selected(a))
                row_layout.addWidget(button)
                self.anchor_buttons[anchor] = button
            layout.addLayout(row_layout)

        layout.addStretch()
        return group

    # Export group ------------------
    def _build_export_group(self) -> QWidget:
        group = QGroupBox("导出设置")
        layout = QVBoxLayout(group)

        form = QFormLayout()
        self.format_combo = QComboBox()
        self.format_combo.addItems(["png", "jpeg"])
        form.addRow("输出格式", self.format_combo)

        output_layout = QHBoxLayout()
        self.output_dir_edit = QLineEdit()
        self.output_dir_edit.setReadOnly(True)
        output_button = QPushButton("选择文件夹")
        output_layout.addWidget(self.output_dir_edit)
        output_layout.addWidget(output_button)
        form.addRow("输出位置", output_layout)

        naming_layout = QVBoxLayout()
        self.naming_keep_radio = QRadioButton("保留原文件名")
        self.naming_prefix_radio = QRadioButton("添加前缀")
        self.naming_suffix_radio = QRadioButton("添加后缀")
        self.naming_suffix_radio.setChecked(True)
        naming_layout.addWidget(self.naming_keep_radio)
        naming_layout.addWidget(self.naming_prefix_radio)
        naming_layout.addWidget(self.naming_suffix_radio)
        self.naming_group = QButtonGroup(self)
        self.naming_group.addButton(self.naming_keep_radio, id=0)
        self.naming_group.addButton(self.naming_prefix_radio, id=1)
        self.naming_group.addButton(self.naming_suffix_radio, id=2)

        prefix_layout = QHBoxLayout()
        self.prefix_edit = QLineEdit("wm_")
        prefix_layout.addWidget(QLabel("前缀"))
        prefix_layout.addWidget(self.prefix_edit)
        naming_layout.addLayout(prefix_layout)

        suffix_layout = QHBoxLayout()
        self.suffix_edit = QLineEdit("_watermarked")
        suffix_layout.addWidget(QLabel("后缀"))
        suffix_layout.addWidget(self.suffix_edit)
        naming_layout.addLayout(suffix_layout)

        form.addRow("命名规则", naming_layout)

        quality_layout = QHBoxLayout()
        self.jpeg_quality_slider = QSlider(Qt.Horizontal)
        self.jpeg_quality_slider.setRange(10, 100)
        self.jpeg_quality_slider.setValue(90)
        self.jpeg_quality_spin = QSpinBox()
        self.jpeg_quality_spin.setRange(10, 100)
        self.jpeg_quality_spin.setValue(90)
        quality_layout.addWidget(self.jpeg_quality_slider)
        quality_layout.addWidget(self.jpeg_quality_spin)
        form.addRow("JPEG质量", quality_layout)

        resize_layout = QHBoxLayout()
        self.resize_combo = QComboBox()
        self.resize_combo.addItems(["不缩放", "按宽度", "按高度", "按比例%"])
        self.resize_value_spin = QSpinBox()
        self.resize_value_spin.setRange(1, 10000)
        resize_layout.addWidget(self.resize_combo)
        resize_layout.addWidget(self.resize_value_spin)
        form.addRow("尺寸调整", resize_layout)

        layout.addLayout(form)

        output_button.clicked.connect(self.browseOutputDirRequested.emit)
        self.format_combo.currentTextChanged.connect(self._on_export_changed)
        self.naming_group.idToggled.connect(self._on_export_changed)
        self.prefix_edit.textChanged.connect(self._on_export_changed)
        self.suffix_edit.textChanged.connect(self._on_export_changed)
        self.jpeg_quality_slider.valueChanged.connect(self.jpeg_quality_spin.setValue)
        self.jpeg_quality_spin.valueChanged.connect(self.jpeg_quality_slider.setValue)
        self.jpeg_quality_slider.valueChanged.connect(self._on_export_changed)
        self.resize_combo.currentIndexChanged.connect(self._on_export_changed)
        self.resize_value_spin.valueChanged.connect(self._on_export_changed)

        return group

    # Template group ------------------
    def _build_template_group(self) -> QWidget:
        group = QGroupBox("模板管理")
        layout = QVBoxLayout(group)

        combo_layout = QHBoxLayout()
        self.template_combo = QComboBox()
        combo_layout.addWidget(QLabel("模板列表"))
        combo_layout.addWidget(self.template_combo)
        load_button = QPushButton("加载")
        delete_button = QPushButton("删除")
        combo_layout.addWidget(load_button)
        combo_layout.addWidget(delete_button)
        layout.addLayout(combo_layout)

        save_layout = QHBoxLayout()
        self.template_name_edit = QLineEdit()
        save_button = QPushButton("保存为模板")
        save_layout.addWidget(QLabel("模板名称"))
        save_layout.addWidget(self.template_name_edit)
        save_layout.addWidget(save_button)
        layout.addLayout(save_layout)

        load_button.clicked.connect(self._on_template_load)
        delete_button.clicked.connect(self._on_template_delete)
        save_button.clicked.connect(self._on_template_save)

        return group

    # Helpers ------------------
    def _apply_settings_to_ui(self) -> None:
        self.text_input.setText(self._watermark_settings.text_settings.text)
        self.font_combo.setCurrentText(self._watermark_settings.text_settings.font_family)
        self.font_size_spin.setValue(self._watermark_settings.text_settings.font_size)
        self.bold_check.setChecked(self._watermark_settings.text_settings.bold)
        self.italic_check.setChecked(self._watermark_settings.text_settings.italic)
        self.opacity_slider.setValue(self._watermark_settings.text_settings.opacity)
        self.shadow_check.setChecked(self._watermark_settings.text_settings.shadow_enabled)
        self.outline_check.setChecked(self._watermark_settings.text_settings.outline_enabled)
        self.outline_width_spin.setValue(self._watermark_settings.text_settings.outline_width)
        self._update_color_preview(color_to_qcolor(self._watermark_settings.text_settings.color))

        if self._watermark_settings.watermark_type == WatermarkType.TEXT:
            self.watermark_stack.setCurrentIndex(0)
            self.text_radio.setChecked(True)
        else:
            self.watermark_stack.setCurrentIndex(1)
            self.image_radio.setChecked(True)

        self.rotation_slider.setValue(int(self._watermark_settings.rotation))
        self.rotation_spin.setValue(int(self._watermark_settings.rotation))

        image_settings = self._watermark_settings.image_settings
        if image_settings.image_path:
            self.image_path_edit.setText(image_settings.image_path)
        self.image_scale_slider.setValue(int(image_settings.scale * 100))
        self.image_opacity_slider.setValue(image_settings.opacity)

        export = self._export_settings
        self.format_combo.setCurrentText(export.output_format.lower())
        if export.output_dir:
            self.output_dir_edit.setText(export.output_dir)
        if export.naming_mode == ExportNamingMode.KEEP_ORIGINAL:
            self.naming_keep_radio.setChecked(True)
        elif export.naming_mode == ExportNamingMode.PREFIX:
            self.naming_prefix_radio.setChecked(True)
        else:
            self.naming_suffix_radio.setChecked(True)
        self.prefix_edit.setText(export.custom_prefix)
        self.suffix_edit.setText(export.custom_suffix)
        self.prefix_edit.setEnabled(export.naming_mode == ExportNamingMode.PREFIX)
        self.suffix_edit.setEnabled(export.naming_mode == ExportNamingMode.SUFFIX)
        self.jpeg_quality_slider.setValue(export.jpeg_quality)
        self.jpeg_quality_spin.setValue(export.jpeg_quality)
        is_jpeg = export.output_format.lower() in ("jpeg", "jpg")
        self.jpeg_quality_slider.setEnabled(is_jpeg)
        self.jpeg_quality_spin.setEnabled(is_jpeg)
        resize_map = {
            ResizeMode.NONE: 0,
            ResizeMode.WIDTH: 1,
            ResizeMode.HEIGHT: 2,
            ResizeMode.PERCENT: 3,
        }
        self.resize_combo.setCurrentIndex(resize_map.get(export.resize_mode, 0))
        if export.resize_value:
            self.resize_value_spin.setValue(int(export.resize_value))

        for anchor, button in self.anchor_buttons.items():
            button.setChecked(anchor == self._watermark_settings.layout.anchor)

    def _update_color_preview(self, color: QColor) -> None:
        palette = self.color_preview.palette()
        palette.setColor(self.color_preview.backgroundRole(), color)
        self.color_preview.setPalette(palette)

    def set_templates(self, names: List[str]) -> None:
        self._template_names = names
        self.template_combo.clear()
        self.template_combo.addItems(names)

    def set_output_directory(self, directory: str) -> None:
        self._export_settings.output_dir = directory
        self.output_dir_edit.setText(directory)
        self.exportChanged.emit(replace(self._export_settings))

    def set_watermark_image_path(self, path: str) -> None:
        self.image_path_edit.setText(path)

    def set_settings(self, watermark: WatermarkSettings, export: ExportSettings) -> None:
        self._watermark_settings = watermark
        self._export_settings = export
        self._apply_settings_to_ui()
        self.watermarkChanged.emit(replace(self._watermark_settings))
        self.exportChanged.emit(replace(self._export_settings))

    # Change handlers ------------------
    def _on_watermark_type_changed(self, button_id: int, checked: bool) -> None:
        if not checked:
            return
        if button_id == 0:
            self._watermark_settings.watermark_type = WatermarkType.TEXT
            self.watermark_stack.setCurrentIndex(0)
        else:
            self._watermark_settings.watermark_type = WatermarkType.IMAGE
            self.watermark_stack.setCurrentIndex(1)
        self.watermarkChanged.emit(replace(self._watermark_settings))

    def _on_text_settings_changed(self, *args) -> None:
        settings = self._watermark_settings.text_settings
        settings.text = self.text_input.text()
        settings.font_family = self.font_combo.currentText()
        settings.font_size = self.font_size_spin.value()
        settings.bold = self.bold_check.isChecked()
        settings.italic = self.italic_check.isChecked()
        settings.opacity = self.opacity_slider.value()
        settings.shadow_enabled = self.shadow_check.isChecked()
        settings.outline_enabled = self.outline_check.isChecked()
        settings.outline_width = self.outline_width_spin.value()
        self._watermark_settings.text_settings = settings
        self.watermarkChanged.emit(replace(self._watermark_settings))

    def _on_color_clicked(self) -> None:
        initial = color_to_qcolor(self._watermark_settings.text_settings.color)
        options = QColorDialog.ColorDialogOption.ShowAlphaChannel | QColorDialog.ColorDialogOption.DontUseNativeDialog
        color = QColorDialog.getColor(initial, self, "选择颜色", options)
        if color.isValid():
            self._watermark_settings.text_settings.color = qcolor_to_tuple(color)
            self._update_color_preview(color)
            self.watermarkChanged.emit(replace(self._watermark_settings))

    def _on_image_settings_changed(self, *args) -> None:
        settings = self._watermark_settings.image_settings
        settings.image_path = self.image_path_edit.text() or None
        settings.scale = self.image_scale_slider.value() / 100.0
        settings.opacity = self.image_opacity_slider.value()
        self._watermark_settings.image_settings = settings
        self.watermarkChanged.emit(replace(self._watermark_settings))

    def _on_rotation_changed(self, value: int) -> None:
        self._watermark_settings.rotation = float(value)
        self.watermarkChanged.emit(replace(self._watermark_settings))

    def _on_anchor_selected(self, anchor: WatermarkAnchor) -> None:
        for a, button in self.anchor_buttons.items():
            button.setChecked(a == anchor)
        self._watermark_settings.layout.anchor = anchor
        position_map = {
            WatermarkAnchor.TOP_LEFT: (0.05, 0.05),
            WatermarkAnchor.TOP_CENTER: (0.5, 0.05),
            WatermarkAnchor.TOP_RIGHT: (0.95, 0.05),
            WatermarkAnchor.CENTER_LEFT: (0.05, 0.5),
            WatermarkAnchor.CENTER: (0.5, 0.5),
            WatermarkAnchor.CENTER_RIGHT: (0.95, 0.5),
            WatermarkAnchor.BOTTOM_LEFT: (0.05, 0.95),
            WatermarkAnchor.BOTTOM_CENTER: (0.5, 0.95),
            WatermarkAnchor.BOTTOM_RIGHT: (0.95, 0.95),
        }
        self._watermark_settings.layout.position = position_map[anchor]
        self.watermarkChanged.emit(replace(self._watermark_settings))
        self.anchorSelected.emit(anchor)

    def _on_export_changed(self, *args) -> None:
        export = self._export_settings
        export.output_format = self.format_combo.currentText().lower()
        selected_id = self.naming_group.checkedId()
        if selected_id == 0:
            export.naming_mode = ExportNamingMode.KEEP_ORIGINAL
        elif selected_id == 1:
            export.naming_mode = ExportNamingMode.PREFIX
        else:
            export.naming_mode = ExportNamingMode.SUFFIX
        export.custom_prefix = self.prefix_edit.text()
        export.custom_suffix = self.suffix_edit.text()
        export.jpeg_quality = self.jpeg_quality_slider.value()
        is_jpeg = export.output_format == "jpeg"
        self.jpeg_quality_slider.setEnabled(is_jpeg)
        self.jpeg_quality_spin.setEnabled(is_jpeg)
        self.prefix_edit.setEnabled(export.naming_mode == ExportNamingMode.PREFIX)
        self.suffix_edit.setEnabled(export.naming_mode == ExportNamingMode.SUFFIX)
        resize_index = self.resize_combo.currentIndex()
        resize_mapping = {
            0: ResizeMode.NONE,
            1: ResizeMode.WIDTH,
            2: ResizeMode.HEIGHT,
            3: ResizeMode.PERCENT,
        }
        export.resize_mode = resize_mapping.get(resize_index, ResizeMode.NONE)
        export.resize_value = self.resize_value_spin.value()
        self.exportChanged.emit(replace(export))

    def _on_template_save(self) -> None:
        name = self.template_name_edit.text().strip()
        if name:
            self.saveTemplateRequested.emit(name)

    def _on_template_load(self) -> None:
        name = self.template_combo.currentText()
        if name:
            self.loadTemplateRequested.emit(name)

    def _on_template_delete(self) -> None:
        name = self.template_combo.currentText()
        if name:
            self.deleteTemplateRequested.emit(name)

    def update_layout(self, layout: WatermarkLayout) -> None:
        self._watermark_settings.layout = layout
        for anchor, button in self.anchor_buttons.items():
            button.setChecked(anchor == layout.anchor)

    def current_settings(self) -> tuple[WatermarkSettings, ExportSettings]:
        return replace(self._watermark_settings), replace(self._export_settings)


