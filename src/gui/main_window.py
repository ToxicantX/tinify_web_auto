from PySide6.QtWidgets import (QMainWindow, QTabWidget, QStatusBar, QMenuBar,
                                QMenu, QMessageBox)
from PySide6.QtGui import QAction
from PySide6.QtCore import Qt, QTimer

from src.data.settings_manager import SettingsManager
from src.data import database
from src.gui.compress_tab import CompressTab
from src.gui.history_tab import HistoryTab
from src.gui.settings_dialog import SettingsDialog


class MainWindow(QMainWindow):

    def __init__(self):
        super().__init__()
        self._settings = SettingsManager()

        database.init_db()

        self._init_ui()

    def _init_ui(self):
        self.setWindowTitle("TinyPNG 批量压缩工具")
        self.setMinimumSize(900, 650)
        self.resize(1000, 720)

        # Menu bar
        menubar = self.menuBar()

        file_menu = menubar.addMenu("文件(&F)")

        exit_action = QAction("退出(&Q)", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        settings_menu = menubar.addMenu("设置(&S)")
        settings_action = QAction("打开设置(&O)", self)
        settings_action.triggered.connect(self._open_settings)
        settings_menu.addAction(settings_action)

        help_menu = menubar.addMenu("帮助(&H)")
        about_action = QAction("关于(&A)", self)
        about_action.triggered.connect(self._show_about)
        help_menu.addAction(about_action)

        # Tabs
        self._tabs = QTabWidget()
        self._compress_tab = CompressTab(self._settings)
        self._history_tab = HistoryTab()

        self._tabs.addTab(self._compress_tab, "压缩")
        self._tabs.addTab(self._history_tab, "历史记录")

        # Refresh history when switching to that tab
        self._tabs.currentChanged.connect(self._on_tab_changed)

        self.setCentralWidget(self._tabs)

        # Status bar
        self._status_bar = QStatusBar()
        self.setStatusBar(self._status_bar)
        self._status_bar.showMessage("就绪")

        self._compress_tab.status_message.connect(self._show_status)

    def _open_settings(self):
        dlg = SettingsDialog(self._settings, self)
        if dlg.exec():
            self._status_bar.showMessage("设置已保存", 3000)

    def _show_about(self):
        QMessageBox.about(
            self, "关于 TinyPNG 批量压缩工具",
            "<h3>TinyPNG 批量压缩工具 v1.0</h3>"
            "<p>基于 TinyPNG (tinify) API 的桌面批量图片压缩工具。</p>"
            "<p>支持 PNG / JPG / WebP / AVIF 格式。</p>"
            "<p>API 模式: 使用官方 tinify API (每月500次免费)<br>"
            "网页模式: 自动化 tinypng.com 网页操作</p>"
        )

    def _on_tab_changed(self, index: int):
        if index == 1:  # History tab
            self._history_tab.refresh()

    def _show_status(self, message: str, timeout: int):
        self._status_bar.showMessage(message, timeout)
