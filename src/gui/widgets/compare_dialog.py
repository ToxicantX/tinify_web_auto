from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel,
                                QPushButton, QDialogButtonBox)
from PySide6.QtGui import QPixmap
from PySide6.QtCore import Qt
from PIL import Image
import io


class CompareDialog(QDialog):

    def __init__(self, original_path: str, compressed_path: str, parent=None):
        super().__init__(parent)
        self.original_path = original_path
        self.compressed_path = compressed_path
        self._init_ui()

    def _init_ui(self):
        self.setWindowTitle("压缩前后对比")
        self.setMinimumSize(800, 500)

        layout = QVBoxLayout(self)

        # Images side by side
        image_layout = QHBoxLayout()

        # Original
        orig_layout = QVBoxLayout()
        orig_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        orig_img = self._load_preview(self.original_path, 350)
        orig_label = QLabel()
        orig_label.setPixmap(orig_img)
        orig_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        orig_label.setFixedSize(360, 360)
        orig_label.setStyleSheet("border: 1px solid #ddd; background: white;")
        orig_size = QLabel(f"原始: {self._fmt_size(self.original_path)}")
        orig_size.setAlignment(Qt.AlignmentFlag.AlignCenter)
        orig_size.setStyleSheet("font-weight: bold;")
        orig_layout.addWidget(orig_label)
        orig_layout.addWidget(orig_size)

        # Compressed
        comp_layout = QVBoxLayout()
        comp_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        comp_img = self._load_preview(self.compressed_path, 350)
        comp_label = QLabel()
        comp_label.setPixmap(comp_img)
        comp_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        comp_label.setFixedSize(360, 360)
        comp_label.setStyleSheet("border: 1px solid #ddd; background: white;")
        comp_size = QLabel(f"压缩后: {self._fmt_size(self.compressed_path)}")
        comp_size.setAlignment(Qt.AlignmentFlag.AlignCenter)
        comp_size.setStyleSheet("font-weight: bold; color: #4CAF50;")
        comp_layout.addWidget(comp_label)
        comp_layout.addWidget(comp_size)

        image_layout.addLayout(orig_layout)
        image_layout.addLayout(comp_layout)

        # Stats
        import os
        osize = os.path.getsize(self.original_path)
        csize = os.path.getsize(self.compressed_path)
        ratio = round((1 - csize / osize) * 100, 1) if osize > 0 else 0
        stats = QLabel(f"压缩率: {ratio}%  |  节省: {self._fmt_size_abs(osize - csize)}")
        stats.setAlignment(Qt.AlignmentFlag.AlignCenter)
        stats.setStyleSheet("font-size: 14px; margin: 8px;")

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok)
        buttons.accepted.connect(self.accept)

        layout.addLayout(image_layout)
        layout.addWidget(stats)
        layout.addWidget(buttons)

    def _load_preview(self, path: str, max_size: int) -> QPixmap:
        try:
            img = Image.open(path)
            img.thumbnail((max_size, max_size), Image.LANCZOS)
            data = io.BytesIO()
            img.save(data, format="PNG")
            pix = QPixmap()
            pix.loadFromData(data.getvalue())
            return pix
        except Exception:
            return QPixmap()

    @staticmethod
    def _fmt_size(path: str) -> str:
        import os
        size = os.path.getsize(path)
        return CompareDialog._fmt_size_abs(size)

    @staticmethod
    def _fmt_size_abs(size: int) -> str:
        for unit in ["B", "KB", "MB", "GB"]:
            if abs(size) < 1024:
                return f"{size:.1f} {unit}"
            size /= 1024
        return f"{size:.1f} TB"
