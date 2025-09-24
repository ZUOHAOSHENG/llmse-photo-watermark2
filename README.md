# 批量图片水印工具

一个使用 Python 与 Qt (PySide6) 构建的桌面应用，可在 Windows 与 macOS 上本地批量为图片添加文本或图片水印，并支持模板保存、实时预览以及灵活的导出设置。

## 功能概览
- **图片导入**：支持拖拽、文件选择器、多选与整目录导入；左侧列表显示缩略图与文件名。
- **水印类型**：
  - 文本水印：可配置内容、字体、字号、粗体/斜体、颜色（含透明度）、阴影、描边、旋转角度。
  - 图片水印：支持带透明通道 PNG，比例缩放与透明度调节。
- **布局与预览**：九宫格快速定位，预览区实时更新，并支持直接拖拽水印到任意位置。
- **导出设置**：
  - 输出格式（PNG / JPEG）、JPEG 质量调节。
  - 输出目录选择，默认阻止覆盖原始目录。
  - 文件命名规则（原名 / 前缀 / 后缀）。
  - 可选尺寸调整（目标宽度、高度或百分比缩放）。
- **模板管理**：保存/加载/删除水印配置，启动时自动恢复上次关闭时的设置。

## 环境准备
1. 安装 Python 3.10+。
2. （推荐）为项目创建虚拟环境：
   ```powershell
   conda create -y -n watermark python=3.11
   conda activate watermark
   ```
3. 安装依赖：
   ```powershell
   pip install -r requirements.txt
   ```

## 运行
在仓库根目录执行：
```powershell
python -m watermark_app
```
若系统安装了 PySide6 运行库，将弹出应用主窗口。

> **提示**：首次运行前请确保当前终端已经激活了安装依赖时使用的虚拟环境，否则会提示找不到 `PySide6`。

## 打包发布（可选）
可以使用 [PyInstaller](https://pyinstaller.org/) 打包成单文件或目录形式的可执行程序：
```powershell
pyinstaller --noconsole --name watermark-tool --icon icon.ico -m watermark_app
```
`icon.ico` 为可选图标。打包完成后可将 `dist/watermark-tool` 目录（或单文件）打包上传到 GitHub Release 供下载。

## 目录结构
```
├─README.md
├─requirements.txt
└─watermark_app
    ├─__init__.py
    ├─__main__.py
    ├─app.py
    ├─export_settings.py
    ├─image_manager.py
    ├─main.py
    ├─main_window.py
    ├─settings_store.py
    ├─template_manager.py
    ├─utils.py
    ├─watermark_renderer.py
    ├─watermark_settings.py
    └─widgets
        ├─controls_panel.py
        ├─image_list_widget.py
        └─preview_widget.py
```

## 存储说明
- **模板文件**、**最近一次配置**默认保存在用户目录下的 `.llmse_watermark/` 中，多个工程共用同一套模板。

## 后续工作建议
- 增加导出进度条与取消操作。
- 添加对更多图片格式及 CMYK JPEG 的兼容处理。
- 支持命令行批处理模式，便于脚本调用。

祝开发顺利！
