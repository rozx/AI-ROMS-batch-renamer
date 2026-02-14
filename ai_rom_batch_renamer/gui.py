"""GUI entry module for ROM batch renamer."""

import codecs
import os
import re
import shlex
import sys
from pathlib import Path

from PySide6.QtCore import QProcess, QProcessEnvironment, QSettings, QTimer, Qt
from PySide6.QtGui import (
    QColor,
    QDragEnterEvent,
    QDropEvent,
    QIcon,
    QCloseEvent,
    QTextCharFormat,
    QTextCursor,
)
from PySide6.QtWidgets import (  # pylint: disable=no-name-in-module
    QApplication,
    QButtonGroup,
    QCheckBox,
    QFileDialog,
    QFormLayout,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QRadioButton,
    QScrollArea,
    QSizePolicy,
    QSpinBox,
    QSplitter,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from ai_rom_batch_renamer.classes.AIConfig import AIConfig

# ── Colour palette (Tailwind Slate) ──
_BG = "#0F172A"
_CARD = "#1E293B"
_INPUT = "#0F172A"
_BORDER = "#334155"
_BORDER_HI = "#475569"
_BORDER_FOCUS = "#60A5FA"
_TEXT = "#E2E8F0"
_TEXT_DIM = "#94A3B8"
_ACCENT = "#2563EB"
_ACCENT_HI = "#3B82F6"
_ACCENT_DK = "#1D4ED8"
_ANSI_RE = re.compile(r"\x1b\[([0-9;]*)m")
_CONTROL_CHARS_RE = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")
_LINE_INDICATOR = "▶ "
_FILE_LIST_SEPARATOR = ";"


def _resolve_icon_path() -> str | None:
    candidates = [
        Path("assets") / "icos" / "icon.ico",
        Path("assets") / "icos" / "icon.png",
    ]
    for path in candidates:
        if path.is_file():
            return str(path)
    return None

_STYLESHEET = f"""
/* ═══ Window ═══ */
QMainWindow {{
    background: {_BG};
}}

/* ═══ Cards ═══ */
QGroupBox {{
    background: {_CARD};
    border: 1px solid {_BORDER};
    border-radius: 12px;
    margin-top: 16px;
    padding: 16px 14px 12px 14px;
    color: {_TEXT};
    font-size: 13px;
}}
QGroupBox::title {{
    subcontrol-origin: margin;
    left: 14px;
    padding: 0 8px;
    color: #93C5FD;
    font-weight: 700;
    font-size: 13px;
}}

/* ═══ Inputs ═══ */
QLineEdit, QSpinBox {{
    background: {_INPUT};
    border: 1px solid {_BORDER};
    border-radius: 8px;
    padding: 7px 10px;
    color: {_TEXT};
    selection-background-color: {_ACCENT};
    min-height: 18px;
    font-size: 13px;
}}
QLineEdit:focus, QSpinBox:focus {{
    border: 1.5px solid {_BORDER_FOCUS};
}}
QLineEdit:hover, QSpinBox:hover {{
    border-color: {_BORDER_HI};
}}

/* ═══ Log ═══ */
QTextEdit {{
    background: #020617;
    border: 1px solid {_BORDER};
    border-radius: 10px;
    padding: 8px;
    color: #CBD5E1;
    selection-background-color: {_ACCENT};
    font-size: 13px;
}}

/* ═══ Checkboxes ═══ */
QCheckBox {{
    spacing: 8px;
    padding: 5px 10px;
    color: {_TEXT};
    font-size: 13px;
}}
QCheckBox::indicator {{
    width: 18px;
    height: 18px;
    border-radius: 5px;
    border: 1.5px solid {_BORDER_HI};
    background: {_INPUT};
}}
QCheckBox::indicator:checked {{
    background: {_ACCENT};
    border-color: {_ACCENT_HI};
}}
QCheckBox::indicator:hover {{
    border-color: {_BORDER_FOCUS};
}}

/* ═══ Segmented mode toggle ═══ */
QRadioButton#ModeL, QRadioButton#ModeR {{
    background: {_INPUT};
    border: 1.5px solid {_BORDER};
    padding: 8px 20px;
    font-weight: 600;
    font-size: 13px;
    min-width: 90px;
    color: {_TEXT_DIM};
}}
QRadioButton#ModeL {{
    border-top-left-radius: 10px;
    border-bottom-left-radius: 10px;
    border-right: none;
}}
QRadioButton#ModeR {{
    border-top-right-radius: 10px;
    border-bottom-right-radius: 10px;
}}
QRadioButton#ModeL::indicator, QRadioButton#ModeR::indicator {{
    width: 0;
    height: 0;
}}
QRadioButton#ModeL:hover, QRadioButton#ModeR:hover {{
    background: {_CARD};
    border-color: {_BORDER_HI};
}}
QRadioButton#ModeL:checked, QRadioButton#ModeR:checked {{
    background: {_ACCENT_DK};
    border-color: {_ACCENT};
    color: #FFF;
}}

/* ═══ Buttons ═══ */
QPushButton {{
    background: {_CARD};
    border: 1px solid {_BORDER};
    border-radius: 10px;
    padding: 9px 20px;
    font-weight: 600;
    font-size: 13px;
    min-height: 20px;
    color: {_TEXT};
}}
QPushButton:hover {{
    background: {_BORDER};
    border-color: {_BORDER_HI};
}}
QPushButton:pressed {{
    background: {_BORDER_HI};
}}
QPushButton:disabled {{
    color: {_BORDER_HI};
    background: {_INPUT};
    border-color: {_CARD};
}}

QPushButton#Primary {{
    background: {_ACCENT};
    border-color: {_ACCENT_DK};
    color: #FFF;
    padding: 10px 30px;
    font-size: 14px;
}}
QPushButton#Primary:hover {{
    background: {_ACCENT_HI};
    border-color: {_ACCENT};
}}
QPushButton#Primary:pressed {{
    background: {_ACCENT_DK};
}}

QPushButton#Danger {{
    background: #7F1D1D;
    border-color: #991B1B;
    color: #FCA5A5;
}}
QPushButton#Danger:hover {{
    background: #991B1B;
}}
QPushButton#Danger:disabled {{
    background: {_CARD};
    border-color: {_BORDER};
    color: {_BORDER_HI};
}}

QPushButton#Tool {{
    background: transparent;
    border: 1px solid {_BORDER};
    border-radius: 6px;
    padding: 4px 14px;
    font-size: 12px;
    font-weight: 500;
    min-height: 14px;
    color: {_TEXT_DIM};
}}
QPushButton#Tool:hover {{
    background: {_CARD};
    color: {_TEXT};
}}

/* ═══ Labels ═══ */
QLabel {{
    background: transparent;
    color: {_TEXT};
    font-size: 13px;
}}
QLabel#Dim {{
    color: {_TEXT_DIM};
    font-weight: 500;
}}
QLabel#Head {{
    color: #CBD5E1;
    font-weight: 700;
    font-size: 13px;
}}

QLabel#StatusOK {{
    background: {_CARD};
    border: 1px solid {_BORDER};
    border-radius: 10px;
    padding: 8px 14px;
    color: #93C5FD;
    font-weight: 500;
}}
QLabel#StatusRun {{
    background: #172554;
    border: 1px solid #1E40AF;
    border-radius: 10px;
    padding: 8px 14px;
    color: {_BORDER_FOCUS};
    font-weight: 600;
}}
QLabel#StatusGood {{
    background: #052E16;
    border: 1px solid #166534;
    border-radius: 10px;
    padding: 8px 14px;
    color: #4ADE80;
    font-weight: 600;
}}
QLabel#StatusBad {{
    background: #450A0A;
    border: 1px solid #991B1B;
    border-radius: 10px;
    padding: 8px 14px;
    color: #FCA5A5;
    font-weight: 600;
}}

/* ═══ Splitter ═══ */
QSplitter::handle {{
    background: transparent;
    width: 6px;
    height: 6px;
}}
QSplitter::handle:hover {{
    background: {_BORDER};
    border-radius: 3px;
}}

QScrollArea {{
    background: transparent;
    border: none;
}}

/* ═══ Scrollbars ═══ */
QScrollBar:vertical {{
    background: {_BG};
    width: 8px;
    border-radius: 4px;
}}
QScrollBar::handle:vertical {{
    background: {_BORDER};
    border-radius: 4px;
    min-height: 30px;
}}
QScrollBar::handle:vertical:hover {{
    background: {_BORDER_HI};
}}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0;
}}
QScrollBar:horizontal {{
    background: {_BG};
    height: 8px;
    border-radius: 4px;
}}
QScrollBar::handle:horizontal {{
    background: {_BORDER};
    border-radius: 4px;
    min-width: 30px;
}}
QScrollBar::handle:horizontal:hover {{
    background: {_BORDER_HI};
}}
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
    width: 0;
}}
"""


class _DropLineEdit(QLineEdit):
    """QLineEdit subclass that accepts drag-and-drop of files / folders."""

    def __init__(self, *args, **kwargs) -> None:  # noqa: ANN002,ANN003
        super().__init__(*args, **kwargs)
        self.setAcceptDrops(True)

    def dragEnterEvent(self, event: QDragEnterEvent) -> None:  # noqa: N802
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event: QDropEvent) -> None:  # noqa: N802
        urls = event.mimeData().urls()
        if urls:
            paths = [url.toLocalFile() for url in urls if url.toLocalFile()]
            if paths:
                self.setText(_FILE_LIST_SEPARATOR.join(paths))


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("ROM Batch Renamer")
        icon_path = _resolve_icon_path()
        if icon_path:
            self.setWindowIcon(QIcon(icon_path))
        self.resize(1400, 1000)
        self.setMinimumSize(900, 700)
        self.setAcceptDrops(True)
        self.setStyleSheet(_STYLESHEET)

        self.process = QProcess(self)
        self.process.readyReadStandardOutput.connect(self._on_stdout)
        self.process.readyReadStandardError.connect(self._on_stderr)
        self.process.started.connect(self._on_started)
        self.process.finished.connect(self._on_finished)

        self._stdout_decoder = codecs.getincrementaldecoder("utf-8")(
            errors="replace"
        )
        self._stderr_decoder = codecs.getincrementaldecoder("utf-8")(
            errors="replace"
        )
        self._ansi_state = QTextCharFormat()
        self._reset_ansi_state()
        self._settings = QSettings("rozx", "AI-ROM-Batch-Renamer")

        self._create_widgets()
        self._load_ai_config()
        self._connect_signals()
        self._apply_placeholders()
        self._setup_ui()
        self._load_ui_settings()
        self._on_source_mode_changed(self.directory_mode_radio.isChecked())
        self._on_ai_toggled(self.ai_check.isChecked())

    def _load_ai_config(self) -> None:
        ai_config = AIConfig()
        ai_config.load()

        self.model_input.setText(ai_config.model)
        self.api_key_input.setText(ai_config.apiKey)
        self.endpoint_input.setText(ai_config.endpoint)

    def _save_ai_config(self) -> None:
        ai_config = AIConfig()
        ai_config.model = self.model_input.text().strip()
        ai_config.apiKey = self.api_key_input.text().strip()
        ai_config.endpoint = self.endpoint_input.text().strip()
        ai_config.save()

    def _setting_bool(self, key: str, default: bool = False) -> bool:
        value = self._settings.value(key, default)
        if isinstance(value, bool):
            return value
        if value is None:
            return default
        return str(value).strip().lower() in {"1", "true", "yes", "on"}

    def _load_ui_settings(self) -> None:
        mode = str(self._settings.value("gui/source_mode", "directory"))
        self.directory_mode_radio.setChecked(mode != "file")
        self.file_mode_radio.setChecked(mode == "file")

        self.trim_check.setChecked(self._setting_bool("gui/trim"))
        self.dry_check.setChecked(self._setting_bool("gui/dry_run"))
        self.pinyin_check.setChecked(self._setting_bool("gui/pinyin"))
        self.recursive_check.setChecked(self._setting_bool("gui/recursive"))
        self.unzip_check.setChecked(self._setting_bool("gui/unzip"))
        self.force_check.setChecked(self._setting_bool("gui/force"))
        self.ai_check.setChecked(self._setting_bool("gui/ai"))
        self.ai_no_cache_check.setChecked(self._setting_bool("gui/ai_no_cache"))
        self.delete_files_check.setChecked(self._setting_bool("gui/delete_files"))

        self.password_input.setText(str(self._settings.value("gui/password", "")))
        self.includes_input.setText(str(self._settings.value("gui/includes", "")))
        self.excludes_input.setText(str(self._settings.value("gui/excludes", "")))
        self.platform_input.setText(str(self._settings.value("gui/platform", "")))

        batch_size = self._settings.value("gui/ai_batch_size", 10)
        try:
            self.ai_batch_size_input.setValue(int(batch_size))
        except (TypeError, ValueError):
            self.ai_batch_size_input.setValue(10)

    def _save_ui_settings(self) -> None:
        self._settings.setValue(
            "gui/source_mode",
            "directory" if self.directory_mode_radio.isChecked() else "file",
        )
        self._settings.setValue("gui/trim", self.trim_check.isChecked())
        self._settings.setValue("gui/dry_run", self.dry_check.isChecked())
        self._settings.setValue("gui/pinyin", self.pinyin_check.isChecked())
        self._settings.setValue("gui/recursive", self.recursive_check.isChecked())
        self._settings.setValue("gui/unzip", self.unzip_check.isChecked())
        self._settings.setValue("gui/force", self.force_check.isChecked())
        self._settings.setValue("gui/ai", self.ai_check.isChecked())
        self._settings.setValue("gui/ai_no_cache", self.ai_no_cache_check.isChecked())
        self._settings.setValue("gui/delete_files", self.delete_files_check.isChecked())

        self._settings.setValue("gui/password", self.password_input.text())
        self._settings.setValue("gui/includes", self.includes_input.text())
        self._settings.setValue("gui/excludes", self.excludes_input.text())
        self._settings.setValue("gui/platform", self.platform_input.text())
        self._settings.setValue("gui/ai_batch_size", self.ai_batch_size_input.value())
        self._settings.sync()

    def _create_widgets(self) -> None:
        self.directory_input = _DropLineEdit()
        self.file_input = _DropLineEdit()

        self.directory_mode_radio = QRadioButton("  📂 目录模式")
        self.file_mode_radio = QRadioButton("  📄 文件模式")
        self.directory_mode_radio.setObjectName("ModeL")
        self.file_mode_radio.setObjectName("ModeR")

        self.source_mode_group = QButtonGroup(self)
        self.source_mode_group.addButton(self.directory_mode_radio)
        self.source_mode_group.addButton(self.file_mode_radio)
        self.directory_mode_radio.setChecked(True)

        self.browse_dir_button = QPushButton("浏览...")
        self.browse_file_button = QPushButton("浏览...")

        self.trim_check = QCheckBox("裁剪多余字符")
        self.dry_check = QCheckBox("模拟运行")
        self.pinyin_check = QCheckBox("拼音转换")
        self.recursive_check = QCheckBox("递归子目录")
        self.unzip_check = QCheckBox("自动解压")
        self.force_check = QCheckBox("强制重命名")

        self.ai_check = QCheckBox("启用 AI 重命名")
        self.ai_no_cache_check = QCheckBox("不使用 AI 缓存")

        self.delete_files_check = QCheckBox("同时删除缓存文件")

        self.trim_check.setToolTip("去除文件名中多余的括号、标签等冗余字符")
        self.dry_check.setToolTip("仅预览重命名结果，不实际修改文件")
        self.pinyin_check.setToolTip("将中文文件名转为拼音")
        self.recursive_check.setToolTip("递归处理子目录中的所有文件")
        self.unzip_check.setToolTip("自动解压 ZIP/7z/RAR 压缩包后再重命名")
        self.force_check.setToolTip("强制重命名已处理过的文件（跳过检测）")
        self.ai_check.setToolTip("使用 AI 模型智能识别 ROM 名称")
        self.ai_no_cache_check.setToolTip("跳过 AI 结果缓存，每次重新请求")
        self.delete_files_check.setToolTip("清除缓存时同时删除相关缓存文件")

        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.Password)
        self.includes_input = QLineEdit()
        self.excludes_input = QLineEdit()

        self.model_input = QLineEdit()
        self.api_key_input = QLineEdit()
        self.api_key_input.setEchoMode(QLineEdit.Password)
        self.endpoint_input = QLineEdit()
        self.platform_input = QLineEdit()

        self.ai_batch_size_input = QSpinBox()
        self.ai_batch_size_input.setRange(1, 100)
        self.ai_batch_size_input.setValue(10)

        self.log_output = QTextEdit()
        self.log_output.setReadOnly(True)
        self.log_output.setLineWrapMode(QTextEdit.NoWrap)
        self.log_output.setFontFamily("Consolas")
        self.log_output.setStyleSheet("QTextEdit { line-height: 1.35; }")

        self.status_label = QLabel("  🟢 就绪")
        self.status_label.setObjectName("StatusOK")
        self.status_label.setMinimumHeight(40)
        self.status_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        self.rename_button = QPushButton("  🚀 开始重命名")
        self.rename_button.setObjectName("Primary")
        self.revert_button = QPushButton("  ↩️ 回滚")
        self.clear_cache_button = QPushButton("  🧹 清除缓存")
        self.stop_button = QPushButton("  ⛔ 停止任务")
        self.stop_button.setObjectName("Danger")
        self.stop_button.setEnabled(False)

        self.clear_log_button = QPushButton("🗑 清空日志")
        self.clear_log_button.setObjectName("Tool")
        self.copy_log_button = QPushButton("📋 复制日志")
        self.copy_log_button.setObjectName("Tool")

        self.rename_button.setMinimumWidth(180)
        self.revert_button.setMinimumWidth(120)
        self.clear_cache_button.setMinimumWidth(120)
        self.stop_button.setMinimumWidth(120)

    def _connect_signals(self) -> None:
        self.rename_button.clicked.connect(self.run_rename)
        self.revert_button.clicked.connect(self.run_revert)
        self.clear_cache_button.clicked.connect(self.run_clear_cache)
        self.stop_button.clicked.connect(self.stop_process)
        self.browse_dir_button.clicked.connect(self.choose_directory)
        self.browse_file_button.clicked.connect(self.choose_file)
        self.directory_mode_radio.toggled.connect(self._on_source_mode_changed)
        self.ai_check.toggled.connect(self._on_ai_toggled)
        self.clear_log_button.clicked.connect(self.log_output.clear)
        self.copy_log_button.clicked.connect(self._copy_log)

    def _apply_placeholders(self) -> None:
        self.directory_input.setPlaceholderText(
            "拖拽目录到此处，或点击 [浏览] 选择"
        )
        self.file_input.setPlaceholderText(
            "拖拽多个文件到此处，或点击 [浏览] 多选"
        )
        self.password_input.setPlaceholderText("可选：解压密码")
        self.includes_input.setPlaceholderText("例如：zip,7z,rar（逗号分隔）")
        self.excludes_input.setPlaceholderText("例如：txt,nfo（逗号分隔）")
        self.model_input.setPlaceholderText("例如：gpt-4o-mini")
        self.api_key_input.setPlaceholderText("可选：在此覆盖 apiKey.txt")
        self.endpoint_input.setPlaceholderText("可选：自定义 API Endpoint")
        self.platform_input.setPlaceholderText("例如：PS2 / Switch")

    @staticmethod
    def _dim(text: str) -> QLabel:
        label = QLabel(text)
        label.setObjectName("Dim")
        return label

    def _setup_ui(self) -> None:
        root = QWidget()
        root.setObjectName("root")
        root.setStyleSheet(f"QWidget#root {{ background: {_BG}; }}")

        outer = QVBoxLayout(root)
        outer.setContentsMargins(14, 14, 14, 14)
        outer.setSpacing(8)

        left_content = QWidget()
        left_content.setObjectName("root")
        left_layout = QVBoxLayout(left_content)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(8)
        self.left_panel = left_content

        source_group = QGroupBox("📁 输入源")
        source_layout = QGridLayout()
        source_layout.setHorizontalSpacing(10)
        source_layout.setVerticalSpacing(10)
        source_layout.setColumnStretch(1, 1)

        mode_row = QWidget()
        mode_layout = QHBoxLayout(mode_row)
        mode_layout.setContentsMargins(0, 0, 0, 0)
        mode_layout.setSpacing(0)
        mode_layout.addWidget(self.directory_mode_radio)
        mode_layout.addWidget(self.file_mode_radio)
        mode_layout.addStretch()

        source_layout.addWidget(mode_row, 0, 0, 1, 3)

        self.directory_label = self._dim("目录")
        self.file_label = self._dim("文件")
        source_layout.addWidget(self.directory_label, 1, 0)
        source_layout.addWidget(self.directory_input, 1, 1)
        source_layout.addWidget(self.browse_dir_button, 1, 2)
        source_layout.addWidget(self.file_label, 2, 0)
        source_layout.addWidget(self.file_input, 2, 1)
        source_layout.addWidget(self.browse_file_button, 2, 2)
        source_group.setLayout(source_layout)

        option_group = QGroupBox("⚙️ 基础参数")
        option_layout = QVBoxLayout()
        option_layout.setSpacing(10)

        flags_grid = QGridLayout()
        flags_grid.setHorizontalSpacing(12)
        flags_grid.setVerticalSpacing(2)
        checks = [
            self.trim_check,
            self.dry_check,
            self.pinyin_check,
            self.recursive_check,
            self.unzip_check,
            self.force_check,
        ]
        for index, checkbox in enumerate(checks):
            flags_grid.addWidget(checkbox, index // 3, index % 3)
        option_layout.addLayout(flags_grid)

        form = QFormLayout()
        form.setFieldGrowthPolicy(QFormLayout.AllNonFixedFieldsGrow)
        form.setHorizontalSpacing(12)
        form.setVerticalSpacing(8)
        form.addRow(self._dim("解压密码"), self.password_input)
        form.addRow(self._dim("包含扩展名"), self.includes_input)
        form.addRow(self._dim("排除扩展名"), self.excludes_input)
        option_layout.addLayout(form)
        option_group.setLayout(option_layout)

        ai_group = QGroupBox("🤖 AI 设置")
        ai_layout = QVBoxLayout()
        ai_layout.setSpacing(10)

        ai_row = QHBoxLayout()
        ai_row.addWidget(self.ai_check)
        ai_row.addWidget(self.ai_no_cache_check)
        ai_row.addStretch()
        ai_layout.addLayout(ai_row)

        self.ai_detail_widget = QWidget()
        ai_form = QFormLayout(self.ai_detail_widget)
        ai_form.setFieldGrowthPolicy(QFormLayout.AllNonFixedFieldsGrow)
        ai_form.setHorizontalSpacing(12)
        ai_form.setVerticalSpacing(8)
        ai_form.setContentsMargins(0, 4, 0, 0)
        ai_form.addRow(self._dim("模型"), self.model_input)
        ai_form.addRow(self._dim("API Key"), self.api_key_input)
        ai_form.addRow(self._dim("Endpoint"), self.endpoint_input)
        ai_form.addRow(self._dim("平台"), self.platform_input)
        ai_form.addRow(self._dim("批量大小"), self.ai_batch_size_input)
        ai_layout.addWidget(self.ai_detail_widget)
        ai_group.setLayout(ai_layout)

        source_group.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Maximum)
        option_group.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Maximum)
        ai_group.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Maximum)

        left_layout.addWidget(source_group)
        left_layout.addWidget(option_group)
        left_layout.addWidget(ai_group)

        right = QWidget()
        right.setObjectName("root")
        right_layout = QVBoxLayout(right)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(6)
        self.right_panel = right

        log_header = QHBoxLayout()
        log_label = QLabel("📝 运行日志")
        log_label.setObjectName("Head")
        log_header.addWidget(log_label)
        log_header.addStretch()
        log_header.addWidget(self.clear_log_button)
        log_header.addWidget(self.copy_log_button)
        right_layout.addLayout(log_header)

        self.log_output.setPlaceholderText(
            "📝 运行日志会显示在这里...  💡 提示：可拖拽文件或目录到窗口快速添加"
        )
        self.log_output.setMinimumWidth(500)
        right_layout.addWidget(self.log_output, stretch=1)

        action_row = QHBoxLayout()
        action_row.setSpacing(8)
        action_row.addWidget(self.rename_button)
        action_row.addWidget(self.revert_button)
        action_row.addWidget(self.clear_cache_button)
        action_row.addStretch()
        action_row.addWidget(self.stop_button)

        maintenance_row = QHBoxLayout()
        maintenance_row.setSpacing(8)
        maintenance_row.addWidget(self.delete_files_check)
        maintenance_row.addStretch()

        left_layout.addStretch(1)
        left_layout.addLayout(action_row)
        left_layout.addLayout(maintenance_row)
        left_layout.addWidget(self.status_label)

        left_scroll = QScrollArea()
        left_scroll.setWidgetResizable(True)
        left_scroll.setFrameShape(QScrollArea.NoFrame)
        left_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        left_scroll.setWidget(left_content)

        splitter = QSplitter(Qt.Horizontal)
        splitter.addWidget(left_scroll)
        splitter.addWidget(right)
        splitter.setStretchFactor(0, 5)
        splitter.setStretchFactor(1, 7)
        splitter.setHandleWidth(6)
        splitter.setChildrenCollapsible(False)
        splitter.setCollapsible(0, False)
        splitter.setCollapsible(1, False)
        self.splitter = splitter

        outer.addWidget(splitter, stretch=1)
        self.setCentralWidget(root)

        QTimer.singleShot(0, self._rebalance_splitter)

    def dragEnterEvent(self, event: QDragEnterEvent) -> None:  # noqa: N802
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event: QDropEvent) -> None:  # noqa: N802
        urls = event.mimeData().urls()
        if not urls:
            return

        paths = [url.toLocalFile() for url in urls if url.toLocalFile()]
        if not paths:
            return

        if len(paths) == 1 and os.path.isdir(paths[0]):
            self.directory_mode_radio.setChecked(True)
            self.directory_input.setText(paths[0])
        else:
            self.file_mode_radio.setChecked(True)
            self.file_input.setText(_FILE_LIST_SEPARATOR.join(paths))

    def choose_directory(self) -> None:
        selected = QFileDialog.getExistingDirectory(self, "选择目录")
        if selected:
            self.directory_mode_radio.setChecked(True)
            self.directory_input.setText(selected)

    def choose_file(self) -> None:
        selected_files, _ = QFileDialog.getOpenFileNames(self, "选择文件")
        if selected_files:
            self.file_mode_radio.setChecked(True)
            self.file_input.setText(_FILE_LIST_SEPARATOR.join(selected_files))

    def _copy_log(self) -> None:
        text = self.log_output.toPlainText()
        if text:
            QApplication.clipboard().setText(text)
            self.status_label.setText("  📋 日志已复制到剪贴板")

    def _on_ai_toggled(self, enabled: bool) -> None:
        self.ai_detail_widget.setVisible(enabled)
        self.ai_no_cache_check.setVisible(enabled)
        QTimer.singleShot(0, self._rebalance_splitter)

    def _rebalance_splitter(self) -> None:
        if not hasattr(self, "splitter"):
            return

        total_width = self.splitter.width()
        if total_width <= 0:
            return

        min_log_width = max(500, self.log_output.minimumWidth())
        min_left_width = 460
        left_hint = self.left_panel.sizeHint().width() + 24
        max_left_by_ratio = int(total_width * 0.56)
        max_left_width = max(min_left_width, min(max_left_by_ratio, total_width - min_log_width))
        left_width = min(max(left_hint, min_left_width), max_left_width)
        log_width = max(min_log_width, total_width - left_width)
        self.splitter.setSizes([left_width, log_width])

    def _on_source_mode_changed(self, directory_mode: bool) -> None:
        self.directory_label.setVisible(directory_mode)
        self.directory_input.setVisible(directory_mode)
        self.browse_dir_button.setVisible(directory_mode)

        self.file_label.setVisible(not directory_mode)
        self.file_input.setVisible(not directory_mode)
        self.browse_file_button.setVisible(not directory_mode)

        if directory_mode:
            self.file_input.clear()
        else:
            self.directory_input.clear()

    def _base_command(self) -> list[str]:
        return [sys.executable, "-m", "ai_rom_batch_renamer.main"]

    def _append_option(self, args: list[str], name: str, value: str) -> None:
        normalized = value.strip()
        if normalized:
            args.extend([name, normalized])

    def _append_repeatable(self, args: list[str], name: str, value: str) -> None:
        items = [item.strip() for item in value.split(",") if item.strip()]
        for item in items:
            args.extend([name, item])

    def _build_rename_args(self) -> list[str]:
        args = self._base_command() + ["rename"]

        if self.directory_mode_radio.isChecked():
            self._append_option(args, "--directory", self.directory_input.text())
        else:
            self._append_option(args, "--files", self.file_input.text())

        if self.trim_check.isChecked():
            args.append("--trim")
        if self.dry_check.isChecked():
            args.append("--dry-run")
        if self.pinyin_check.isChecked():
            args.append("--pinyin")
        if self.recursive_check.isChecked():
            args.append("--recursive")
        if self.unzip_check.isChecked():
            args.append("--unzip")
        if self.force_check.isChecked():
            args.append("--force")
        if self.ai_check.isChecked():
            args.append("--ai")
        if self.ai_no_cache_check.isChecked():
            args.append("--ai-no-cache")

        self._append_option(args, "--password", self.password_input.text())
        self._append_repeatable(args, "--includes", self.includes_input.text())
        self._append_repeatable(args, "--excludes", self.excludes_input.text())
        self._append_option(args, "--model", self.model_input.text())
        self._append_option(args, "--api-key", self.api_key_input.text())
        self._append_option(args, "--endpoint", self.endpoint_input.text())
        self._append_option(args, "--platform", self.platform_input.text())
        args.extend(["--ai-batch-size", str(self.ai_batch_size_input.value())])

        return args

    def _build_revert_args(self) -> list[str]:
        args = self._base_command() + ["revert"]

        if self.directory_mode_radio.isChecked():
            self._append_option(args, "--directory", self.directory_input.text())
        else:
            self._append_option(args, "--files", self.file_input.text())

        if self.recursive_check.isChecked():
            args.append("--recursive")
        if self.dry_check.isChecked():
            args.append("--dry-run")

        return args

    def _build_clear_cache_args(self) -> list[str]:
        args = self._base_command() + ["clear-cache", "--yes"]
        if self.delete_files_check.isChecked():
            args.append("--delete-files")
        return args

    def _validate_source(self) -> bool:
        if self.directory_mode_radio.isChecked() and self.directory_input.text().strip():
            return True

        if self.file_mode_radio.isChecked() and self.file_input.text().strip():
            return True

        if self.directory_mode_radio.isChecked():
            QMessageBox.warning(self, "缺少输入", "当前为目录模式，请选择目录。")
            return False

        QMessageBox.warning(self, "缺少输入", "当前为文件模式，请选择文件。")
        return False

    def _set_running_state(self, running: bool) -> None:
        self.rename_button.setEnabled(not running)
        self.revert_button.setEnabled(not running)
        self.clear_cache_button.setEnabled(not running)
        self.stop_button.setEnabled(running)

    def _run(self, command: list[str]) -> None:
        if self.process.state() != QProcess.NotRunning:
            QMessageBox.information(
                self,
                "任务进行中",
                "当前已有任务在运行，请先停止或等待完成。",
            )
            return

        env = QProcessEnvironment.systemEnvironment()
        env.insert("PYTHONIOENCODING", "utf-8")
        env.insert("PYTHONUTF8", "1")
        env.insert("COLUMNS", "240")
        self.process.setProcessEnvironment(env)

        self._stdout_decoder = codecs.getincrementaldecoder("utf-8")(
            errors="replace"
        )
        self._stderr_decoder = codecs.getincrementaldecoder("utf-8")(
            errors="replace"
        )
        self._reset_ansi_state()

        self._append_log_text(f"$ {shlex.join(command)}\n")
        self.process.start(command[0], command[1:])

    def closeEvent(self, event: QCloseEvent) -> None:  # noqa: N802
        self._save_ai_config()
        self._save_ui_settings()
        super().closeEvent(event)

    def run_rename(self) -> None:
        if not self._validate_source():
            return
        self._run(self._build_rename_args())

    def run_revert(self) -> None:
        if not self._validate_source():
            return
        self._run(self._build_revert_args())

    def run_clear_cache(self) -> None:
        self._run(self._build_clear_cache_args())

    def stop_process(self) -> None:
        if self.process.state() != QProcess.NotRunning:
            self.process.kill()
            self._append_log_text("[GUI] 任务已请求终止\n")

    def _on_started(self) -> None:
        self._set_running_state(True)
        self._set_status("  ⏳ 正在执行任务...", "StatusRun")

    def _on_finished(self, exit_code: int, _exit_status: QProcess.ExitStatus) -> None:
        self._set_running_state(False)

        pending_stdout = self._stdout_decoder.decode(b"", final=True)
        if pending_stdout:
            self._append_log_text(pending_stdout)

        pending_stderr = self._stderr_decoder.decode(b"", final=True)
        if pending_stderr:
            self._append_log_text(pending_stderr)

        if exit_code == 0:
            self._set_status("  ✅ 任务完成", "StatusGood")
        else:
            self._set_status(f"  ❌ 任务失败  (exit code {exit_code})", "StatusBad")

    def _set_status(self, text: str, object_name: str) -> None:
        self.status_label.setText(text)
        self.status_label.setObjectName(object_name)
        self.status_label.style().unpolish(self.status_label)
        self.status_label.style().polish(self.status_label)

    def _append_log_text(self, text: str) -> None:
        if not text:
            return

        normalized = self._normalize_log_text(text)
        if not normalized:
            return

        cursor = self.log_output.textCursor()
        cursor.movePosition(QTextCursor.End)

        if "\x1b[" in normalized:
            self._append_ansi_colored_text(cursor, normalized)
        else:
            self._append_keyword_colored_text(cursor, normalized)

        self.log_output.setTextCursor(cursor)
        scrollbar = self.log_output.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

    def _normalize_log_text(self, text: str) -> str:
        normalized = text.replace("\r\n", "\n").replace("\r", "\n")
        return _CONTROL_CHARS_RE.sub("", normalized)

    def _append_keyword_colored_text(self, cursor: QTextCursor, text: str) -> None:
        for line in text.splitlines(keepends=True):
            self._insert_line_indicator(cursor, line)

            lowered = line.lower()
            fmt = QTextCharFormat()
            fmt.setForeground(QColor("#CBD5E1"))

            stripped_line = line.rstrip("\n")
            if " -> " in stripped_line:
                source, target = stripped_line.split(" -> ", maxsplit=1)
                src_fmt = QTextCharFormat()
                src_fmt.setForeground(QColor("#E2E8F0"))
                arrow_fmt = QTextCharFormat()
                arrow_fmt.setForeground(QColor("#67E8F9"))
                dst_fmt = QTextCharFormat()
                dst_fmt.setForeground(QColor("#86EFAC"))

                cursor.insertText(source, src_fmt)
                cursor.insertText(" -> ", arrow_fmt)
                cursor.insertText(target, dst_fmt)
                if line.endswith("\n"):
                    cursor.insertText("\n", fmt)
                continue

            if line.startswith("$ "):
                fmt.setForeground(QColor("#93C5FD"))
            elif any(token in lowered for token in ("error", "failed", "traceback", "❌")):
                fmt.setForeground(QColor("#FCA5A5"))
            elif any(token in lowered for token in ("warning", "warn", "⚠")):
                fmt.setForeground(QColor("#FCD34D"))
            elif any(token in lowered for token in ("success", "done", "completed", "✅")):
                fmt.setForeground(QColor("#86EFAC"))
            elif "[gui]" in lowered:
                fmt.setForeground(QColor("#A5B4FC"))

            cursor.insertText(line, fmt)

    def _append_ansi_colored_text(self, cursor: QTextCursor, text: str) -> None:
        for line in text.splitlines(keepends=True):
            self._insert_line_indicator(cursor, line)

            has_newline = line.endswith("\n")
            segment_text = line[:-1] if has_newline else line

            pos = 0
            for match in _ANSI_RE.finditer(segment_text):
                start, end = match.span()
                if start > pos:
                    segment = segment_text[pos:start]
                    cursor.insertText(segment, self._ansi_state)

                self._apply_ansi_codes(match.group(1))
                pos = end

            if pos < len(segment_text):
                cursor.insertText(segment_text[pos:], self._ansi_state)

            if has_newline:
                plain_fmt = QTextCharFormat()
                plain_fmt.setForeground(QColor("#CBD5E1"))
                cursor.insertText("\n", plain_fmt)

    def _insert_line_indicator(self, cursor: QTextCursor, line: str) -> None:
        indicator_fmt = QTextCharFormat()
        indicator_fmt.setForeground(self._indicator_color_for_line(line))
        cursor.insertText(_LINE_INDICATOR, indicator_fmt)

    def _indicator_color_for_line(self, line: str) -> QColor:
        normalized = _ANSI_RE.sub("", line).lower()

        if line.startswith("$ "):
            return QColor("#93C5FD")
        if any(token in normalized for token in ("error", "failed", "traceback", "❌")):
            return QColor("#FCA5A5")
        if any(token in normalized for token in ("warning", "warn", "⚠")):
            return QColor("#FCD34D")
        if any(token in normalized for token in ("success", "done", "completed", "✅")):
            return QColor("#86EFAC")
        if "[gui]" in normalized:
            return QColor("#A5B4FC")
        if " -> " in normalized:
            return QColor("#67E8F9")
        return QColor("#475569")

    def _apply_ansi_codes(self, code_str: str) -> None:
        parts = [part for part in code_str.split(";") if part]
        if not parts:
            parts = ["0"]

        color_map = {
            30: "#94A3B8",
            31: "#FCA5A5",
            32: "#86EFAC",
            33: "#FCD34D",
            34: "#93C5FD",
            35: "#C4B5FD",
            36: "#67E8F9",
            37: "#E2E8F0",
            90: "#64748B",
            91: "#FCA5A5",
            92: "#86EFAC",
            93: "#FCD34D",
            94: "#93C5FD",
            95: "#C4B5FD",
            96: "#67E8F9",
            97: "#F8FAFC",
        }

        for part in parts:
            if not part.isdigit():
                continue

            code = int(part)
            if code == 0:
                self._reset_ansi_state()
            elif code == 1:
                self._ansi_state.setFontWeight(700)
            elif code == 22:
                self._ansi_state.setFontWeight(400)
            elif code in (39,):
                self._ansi_state.setForeground(QColor("#CBD5E1"))
            elif code in color_map:
                self._ansi_state.setForeground(QColor(color_map[code]))

    def _reset_ansi_state(self) -> None:
        self._ansi_state.setForeground(QColor("#CBD5E1"))
        self._ansi_state.setFontWeight(400)

    def _append_process_text(self, data: bytes, *, stderr: bool = False) -> None:
        if not data:
            return

        decoder = self._stderr_decoder if stderr else self._stdout_decoder
        text = decoder.decode(bytes(data), final=False)
        self._append_log_text(text)

    def _on_stdout(self) -> None:
        self._append_process_text(self.process.readAllStandardOutput().data())

    def _on_stderr(self) -> None:
        self._append_process_text(self.process.readAllStandardError().data(), stderr=True)


def launch_gui() -> int:
    app = QApplication.instance()
    owns_app = app is None
    if app is None:
        app = QApplication(sys.argv)

    icon_path = _resolve_icon_path()
    if icon_path:
        app.setWindowIcon(QIcon(icon_path))

    window = MainWindow()
    window.show()

    if owns_app:
        return app.exec()
    return 0


def main() -> None:
    raise SystemExit(launch_gui())


if __name__ == "__main__":
    main()
