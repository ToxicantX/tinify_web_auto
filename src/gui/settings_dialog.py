from PySide6.QtWidgets import (QDialog, QVBoxLayout, QFormLayout, QLineEdit,
                                QPushButton, QHBoxLayout, QLabel, QSpinBox,
                                QComboBox, QDialogButtonBox, QFileDialog)
from PySide6.QtCore import Qt

from src.core.api_engine import ApiEngine
from src.data.settings_manager import SettingsManager


class SettingsDialog(QDialog):

    def __init__(self, settings: SettingsManager, parent=None):
        super().__init__(parent)
        self._settings = settings
        self._init_ui()

    def _init_ui(self):
        self.setWindowTitle("设置")
        self.setMinimumWidth(460)

        layout = QVBoxLayout(self)

        form = QFormLayout()

        # API Key
        key_layout = QHBoxLayout()
        self._key_input = QLineEdit(self._settings.api_key)
        self._key_input.setEchoMode(QLineEdit.EchoMode.Password)
        self._key_input.setPlaceholderText("输入 TinyPNG API Key")
        key_layout.addWidget(self._key_input)

        self._show_btn = QPushButton("显示")
        self._show_btn.setFixedWidth(50)
        self._show_btn.clicked.connect(self._toggle_key_visibility)
        key_layout.addWidget(self._show_btn)

        self._verify_btn = QPushButton("验证")
        self._verify_btn.setFixedWidth(50)
        self._verify_btn.clicked.connect(self._verify_key)
        key_layout.addWidget(self._verify_btn)

        self._key_status = QLabel("")
        self._key_status.setStyleSheet("font-size: 11px;")

        form.addRow("API Key:", key_layout)
        form.addRow("", self._key_status)

        # Output directory
        dir_layout = QHBoxLayout()
        self._dir_input = QLineEdit(self._settings.output_dir)
        self._dir_input.setPlaceholderText("默认输出目录（留空则输出到原图目录）")
        dir_layout.addWidget(self._dir_input)
        browse_btn = QPushButton("浏览")
        browse_btn.setFixedWidth(60)
        browse_btn.clicked.connect(self._browse_dir)
        dir_layout.addWidget(browse_btn)
        form.addRow("输出目录:", dir_layout)

        # Default mode
        self._mode_combo = QComboBox()
        self._mode_combo.addItem("API 模式", "api")
        self._mode_combo.addItem("网页模式", "web")
        current = self._settings.default_mode
        idx = 0 if current == "api" else 1
        self._mode_combo.setCurrentIndex(idx)
        form.addRow("默认模式:", self._mode_combo)

        # Concurrency
        self._concurrency_spin = QSpinBox()
        self._concurrency_spin.setRange(1, 10)
        self._concurrency_spin.setValue(self._settings.concurrency)
        self._concurrency_spin.setSuffix(" 个并发")
        form.addRow("API 并发数:", self._concurrency_spin)

        # Browser path
        browser_layout = QHBoxLayout()
        self._browser_input = QLineEdit(self._settings.web_browser_path)
        self._browser_input.setPlaceholderText("Chromium 浏览器路径（留空自动检测）")
        browser_layout.addWidget(self._browser_input)
        browser_browse = QPushButton("浏览")
        browser_browse.setFixedWidth(60)
        browser_browse.clicked.connect(self._browse_browser)
        browser_layout.addWidget(browser_browse)
        form.addRow("浏览器路径:", browser_layout)

        layout.addLayout(form)

        # Buttons
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self._save_and_accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _toggle_key_visibility(self):
        if self._key_input.echoMode() == QLineEdit.EchoMode.Password:
            self._key_input.setEchoMode(QLineEdit.EchoMode.Normal)
            self._show_btn.setText("隐藏")
        else:
            self._key_input.setEchoMode(QLineEdit.EchoMode.Password)
            self._show_btn.setText("显示")

    def _verify_key(self):
        key = self._key_input.text().strip()
        if not key:
            self._key_status.setText("请先输入 API Key")
            self._key_status.setStyleSheet("color: #f44336; font-size: 11px;")
            return
        engine = ApiEngine(api_key=key)
        ok, msg = engine.validate()
        if ok:
            self._key_status.setText(msg)
            self._key_status.setStyleSheet("color: #4CAF50; font-size: 11px;")
        else:
            self._key_status.setText(msg)
            self._key_status.setStyleSheet("color: #f44336; font-size: 11px;")

    def _browse_dir(self):
        folder = QFileDialog.getExistingDirectory(self, "选择输出目录")
        if folder:
            self._dir_input.setText(folder)

    def _browse_browser(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "选择浏览器可执行文件", "",
            "Executable (*.exe);;All Files (*)"
        )
        if path:
            self._browser_input.setText(path)

    def _save_and_accept(self):
        self._settings.api_key = self._key_input.text().strip()
        self._settings.output_dir = self._dir_input.text().strip()
        self._settings.default_mode = self._mode_combo.currentData()
        self._settings.concurrency = self._concurrency_spin.value()
        self._settings.web_browser_path = self._browser_input.text().strip()
        self.accept()
