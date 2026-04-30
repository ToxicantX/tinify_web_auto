import os
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                                QFileDialog, QLabel, QMessageBox)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QDragEnterEvent, QDropEvent


class ImageList(QWidget):
    """Image list panel with drag-drop zone."""

    files_dropped = Signal(list)

    SUPPORTED_EXTS = {".png", ".jpg", ".jpeg", ".webp", ".avif"}

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)
        self.setMinimumHeight(120)
        self.setStyleSheet("""
            ImageList {
                border: 2px dashed #aaa;
                border-radius: 8px;
                background: #fafafa;
            }
            ImageList:hover {
                border-color: #4CAF50;
                background: #f0fdf0;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self._icon_label = QLabel("\U0001F5BC")
        self._icon_label.setStyleSheet("font-size: 32px; border: none;")
        self._icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self._text_label = QLabel("拖拽图片文件或文件夹到此处")
        self._text_label.setStyleSheet("font-size: 13px; color: #666; border: none;")
        self._text_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self._sub_label = QLabel("支持 PNG / JPG / WebP / AVIF 格式")
        self._sub_label.setStyleSheet("font-size: 11px; color: #999; border: none;")
        self._sub_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        btn_layout = QHBoxLayout()
        btn_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self._add_btn = QPushButton("添加文件")
        self._add_btn.setFixedWidth(100)
        self._add_btn.clicked.connect(self._on_add_files)

        self._add_dir_btn = QPushButton("添加文件夹")
        self._add_dir_btn.setFixedWidth(100)
        self._add_dir_btn.clicked.connect(self._on_add_folder)

        btn_layout.addWidget(self._add_btn)
        btn_layout.addWidget(self._add_dir_btn)

        layout.addWidget(self._icon_label)
        layout.addWidget(self._text_label)
        layout.addWidget(self._sub_label)
        layout.addLayout(btn_layout)

    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
            self.setStyleSheet(self.styleSheet().replace(
                "border-color: #4CAF50;", "border-color: #2196F3;"))
        else:
            event.ignore()

    def dragLeaveEvent(self, event):
        self.setStyleSheet(self.styleSheet().replace(
            "border-color: #2196F3;", "border-color: #aaa;"))

    def dropEvent(self, event: QDropEvent):
        self.setStyleSheet(self.styleSheet().replace(
            "border-color: #2196F3;", "border-color: #aaa;"))
        files = self._collect_files(event.mimeData().urls())
        if files:
            self.files_dropped.emit(files)
        event.acceptProposedAction()

    def _collect_files(self, urls) -> list[str]:
        result = []
        for url in urls:
            path = url.toLocalFile()
            if os.path.isdir(path):
                for root, _, fs in os.walk(path):
                    for f in fs:
                        if os.path.splitext(f)[1].lower() in self.SUPPORTED_EXTS:
                            result.append(os.path.join(root, f))
            elif os.path.isfile(path):
                if os.path.splitext(path)[1].lower() in self.SUPPORTED_EXTS:
                    result.append(path)
        return result

    def _on_add_files(self):
        files, _ = QFileDialog.getOpenFileNames(
            self, "选择图片文件", "",
            "Images (*.png *.jpg *.jpeg *.webp *.avif);;All Files (*)"
        )
        if files:
            self.files_dropped.emit(files)

    def _on_add_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "选择文件夹")
        if folder:
            files = []
            for root, _, fs in os.walk(folder):
                for f in fs:
                    if os.path.splitext(f)[1].lower() in self.SUPPORTED_EXTS:
                        files.append(os.path.join(root, f))
            if files:
                self.files_dropped.emit(files)
            else:
                QMessageBox.information(self, "提示", "所选文件夹中没有支持的图片文件")
