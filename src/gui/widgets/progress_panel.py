from PySide6.QtWidgets import QWidget, QVBoxLayout, QProgressBar, QLabel


class ProgressPanel(QWidget):

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 4, 0, 4)

        self._status_label = QLabel("就绪")
        self._status_label.setStyleSheet("color: #666; font-size: 12px;")

        self._progress_bar = QProgressBar()
        self._progress_bar.setFixedHeight(22)
        self._progress_bar.setVisible(False)

        layout.addWidget(self._status_label)
        layout.addWidget(self._progress_bar)

    def set_ready(self):
        self._status_label.setText("就绪")
        self._progress_bar.setVisible(False)

    def set_processing(self, completed: int, total: int, current_file: str = ""):
        self._progress_bar.setVisible(True)
        self._progress_bar.setMaximum(total)
        self._progress_bar.setValue(completed)
        self._status_label.setText(f"压缩中 ({completed}/{total}): {current_file}")

    def set_done(self, total: int, total_orig: int, total_comp: int):
        saved_pct = round((1 - total_comp / total_orig) * 100, 1) if total_orig > 0 else 0
        size_saved = self._format_size(total_orig - total_comp)
        self._progress_bar.setVisible(False)
        self._status_label.setText(
            f"完成 {total} 个文件，节省 {saved_pct}% ({size_saved})")

    def set_error(self, msg: str):
        self._progress_bar.setVisible(False)
        self._status_label.setText(f"错误: {msg}")
        self._status_label.setStyleSheet("color: #d32f2f; font-size: 12px;")

    @staticmethod
    def _format_size(size_bytes: int) -> str:
        for unit in ["B", "KB", "MB", "GB"]:
            if abs(size_bytes) < 1024:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024
        return f"{size_bytes:.1f} TB"
