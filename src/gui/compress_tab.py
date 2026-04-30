import os
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                                QTableWidget, QTableWidgetItem, QHeaderView,
                                QFileDialog, QMessageBox, QMenu, QAbstractItemView,
                                QLabel)
from PySide6.QtCore import Qt, Signal, QThread, QObject

from src.gui.widgets.image_list import ImageList
from src.gui.widgets.progress_panel import ProgressPanel
from src.gui.widgets.compare_dialog import CompareDialog
from src.core.base_engine import CompressResult
from src.core.api_engine import ApiEngine
from src.core.web_engine import WebEngine
from src.data.settings_manager import SettingsManager
from src.data import database


class CompressWorker(QObject):
    """Runs compression in background thread."""
    progress = Signal(int, int, str)
    finished = Signal(list)

    def __init__(self, engine, files: list[str], output_dir: str):
        super().__init__()
        self._engine = engine
        self._files = files
        self._output_dir = output_dir

    def run(self):
        results = self._engine.compress_batch(
            self._files, self._output_dir,
            progress_callback=lambda c, t, n: self.progress.emit(c, t, n)
        )
        self.finished.emit(results)


class CompressTab(QWidget):

    status_message = Signal(str, int)

    def __init__(self, settings: SettingsManager, parent=None):
        super().__init__(parent)
        self._settings = settings
        self._files: list[str] = []
        self._results: list[CompressResult] = []
        self._worker: CompressWorker | None = None
        self._thread: QThread | None = None
        self._compressing = False
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)

        # --- Mode switcher ---
        mode_layout = QHBoxLayout()
        mode_label = QLabel("压缩模式:")
        self._mode_btn = QPushButton()
        self._mode_btn.setFixedWidth(140)
        self._mode_btn.clicked.connect(self._toggle_mode)
        self._update_mode_button()
        mode_layout.addWidget(mode_label)
        mode_layout.addWidget(self._mode_btn)
        mode_layout.addStretch()
        layout.addLayout(mode_layout)

        # --- Drop zone ---
        self._drop_zone = ImageList()
        self._drop_zone.files_dropped.connect(self._add_files)
        layout.addWidget(self._drop_zone)

        # --- Output dir ---
        out_layout = QHBoxLayout()
        out_label = QLabel("输出目录:")
        self._output_label = QLabel(self._get_output_dir())
        self._output_label.setStyleSheet("color: #666;")
        out_btn = QPushButton("更改")
        out_btn.setFixedWidth(60)
        out_btn.clicked.connect(self._change_output_dir)
        out_layout.addWidget(out_label)
        out_layout.addWidget(self._output_label)
        out_layout.addStretch()
        out_layout.addWidget(out_btn)
        layout.addLayout(out_layout)

        # --- File table ---
        self._table = QTableWidget(0, 5)
        self._table.setHorizontalHeaderLabels(["文件名", "原始大小", "状态", "压缩后", "压缩率"])
        self._table.horizontalHeader().setStretchLastSection(True)
        self._table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self._table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self._table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self._table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self._table.customContextMenuRequested.connect(self._on_table_menu)
        self._table.setVisible(False)
        layout.addWidget(self._table)

        # --- Action buttons ---
        btn_layout = QHBoxLayout()

        self._clear_btn = QPushButton("清空列表")
        self._clear_btn.clicked.connect(self._clear_files)
        self._clear_btn.setVisible(False)

        self._compress_btn = QPushButton("开始压缩")
        self._compress_btn.setFixedHeight(36)
        self._compress_btn.setStyleSheet("""
            QPushButton {
                background: #4CAF50; color: white; border-radius: 4px;
                font-size: 14px; font-weight: bold;
            }
            QPushButton:hover { background: #388E3C; }
            QPushButton:disabled { background: #ccc; }
        """)
        self._compress_btn.clicked.connect(self._start_compress)
        self._compress_btn.setEnabled(False)

        btn_layout.addWidget(self._clear_btn)
        btn_layout.addStretch()
        btn_layout.addWidget(self._compress_btn)
        layout.addLayout(btn_layout)

        # --- Progress ---
        self._progress_panel = ProgressPanel()
        layout.addWidget(self._progress_panel)

    def _update_mode_button(self):
        mode = self._settings.default_mode
        if mode == "api":
            self._mode_btn.setText("  API 模式")
            self._mode_btn.setStyleSheet("""
                QPushButton {
                    background: #E3F2FD; color: #1565C0; border: 1px solid #90CAF9;
                    border-radius: 4px; padding: 4px 12px; font-weight: bold;
                }
            """)
        else:
            self._mode_btn.setText("  网页模式")
            self._mode_btn.setStyleSheet("""
                QPushButton {
                    background: #FFF3E0; color: #E65100; border: 1px solid #FFCC80;
                    border-radius: 4px; padding: 4px 12px; font-weight: bold;
                }
            """)

    def _toggle_mode(self):
        new_mode = "web" if self._settings.default_mode == "api" else "api"
        self._settings.default_mode = new_mode
        self._update_mode_button()

    def _get_output_dir(self) -> str:
        if self._settings.output_dir:
            return self._settings.output_dir
        return "原图所在目录"

    def _change_output_dir(self):
        folder = QFileDialog.getExistingDirectory(self, "选择输出目录")
        if folder:
            self._settings.output_dir = folder
            self._output_label.setText(folder)

    def _add_files(self, files: list[str]):
        new_files = [f for f in files if f not in self._files]
        if not new_files:
            return
        self._files.extend(new_files)
        self._refresh_table()
        self._drop_zone.setVisible(False)
        self._table.setVisible(True)
        self._clear_btn.setVisible(True)
        self._compress_btn.setEnabled(True)

    def _refresh_table(self):
        self._table.setRowCount(len(self._files))
        for i, f in enumerate(self._files):
            name = os.path.basename(f)
            size_str = self._fmt_size(os.path.getsize(f))
            self._table.setItem(i, 0, QTableWidgetItem(name))
            self._table.setItem(i, 1, QTableWidgetItem(size_str))

            # Keep existing status items if present
            if self._table.item(i, 2) is None:
                self._table.setItem(i, 2, QTableWidgetItem("等待"))
            if self._table.item(i, 3) is None:
                self._table.setItem(i, 3, QTableWidgetItem("-"))
            if self._table.item(i, 4) is None:
                self._table.setItem(i, 4, QTableWidgetItem("-"))

    def _clear_files(self):
        self._files.clear()
        self._results.clear()
        self._table.setRowCount(0)
        self._table.setVisible(False)
        self._drop_zone.setVisible(True)
        self._clear_btn.setVisible(False)
        self._compress_btn.setEnabled(False)
        self._progress_panel.set_ready()

    def _on_table_menu(self, pos):
        rows = set(idx.row() for idx in self._table.selectedIndexes())
        if not rows:
            return
        menu = QMenu(self)
        remove_action = menu.addAction("从列表移除")
        action = menu.exec(self._table.viewport().mapToGlobal(pos))
        if action == remove_action:
            for row in sorted(rows, reverse=True):
                if row < len(self._files):
                    self._files.pop(row)
            self._refresh_table()
            if not self._files:
                self._clear_files()

    def _start_compress(self):
        if self._compressing:
            return
        if not self._files:
            QMessageBox.warning(self, "提示", "请先添加图片文件")
            return

        mode = self._settings.default_mode

        if mode == "api":
            if not self._settings.api_key:
                self.status_message.emit("请先在设置中配置 API Key", 3000)
                return
            engine = ApiEngine(self._settings.api_key, self._settings.concurrency)
        else:
            engine = WebEngine(self._settings.web_browser_path)
            ok, msg = engine.validate()
            if not ok:
                QMessageBox.warning(self, "网页模式错误", msg)
                return

        # Determine output directory
        output_dir = self._settings.output_dir
        if not output_dir:
            output_dir = os.path.dirname(self._files[0])

        self._compressing = True
        self._compress_btn.setEnabled(False)
        self._clear_btn.setEnabled(False)

        self._thread = QThread()
        self._worker = CompressWorker(engine, list(self._files), output_dir)
        self._worker.moveToThread(self._thread)
        self._worker.progress.connect(self._on_progress)
        self._worker.finished.connect(self._on_finished)
        self._thread.started.connect(self._worker.run)
        self._thread.start()

    def _on_progress(self, completed: int, total: int, current_file: str):
        self._progress_panel.set_processing(completed, total, current_file)

    def _on_finished(self, results: list[CompressResult]):
        self._compressing = False
        self._compress_btn.setEnabled(True)
        self._clear_btn.setEnabled(True)
        self._results = results

        # Update table
        for i, r in enumerate(results):
            if r.success:
                self._table.setItem(i, 2, QTableWidgetItem("完成"))
                self._table.item(i, 2).setForeground(Qt.GlobalColor.green)
                self._table.setItem(i, 3, QTableWidgetItem(self._fmt_size(r.compressed_size)))
                self._table.setItem(i, 4, QTableWidgetItem(f"{r.ratio:.1f}%"))
            else:
                self._table.setItem(i, 2, QTableWidgetItem(f"失败: {r.error}"))
                self._table.item(i, 2).setForeground(Qt.GlobalColor.red)

        # Calculate totals
        total_orig = sum(r.original_size for r in results if r.success)
        total_comp = sum(r.compressed_size for r in results if r.success)
        success_count = sum(1 for r in results if r.success)

        # Save to database
        mode = self._settings.default_mode
        for r in results:
            if r.success:
                database.add_record(
                    r.original_path, r.original_name, r.original_size,
                    r.compressed_size, r.output_path, r.duration_ms, mode
                )

        if success_count > 0:
            self._progress_panel.set_done(success_count, total_orig, total_comp)
            failed = len(results) - success_count
            msg = f"成功压缩 {success_count} 个文件"
            if failed:
                msg += f"，{failed} 个失败"
            self.status_message.emit(msg, 5000)
        else:
            self._progress_panel.set_error("所有文件压缩失败")
            self.status_message.emit("压缩失败，请检查设置", 5000)

        self._thread.quit()
        self._thread.wait()
        self._thread = None
        self._worker = None

    @staticmethod
    def _fmt_size(size_bytes: int) -> str:
        for unit in ["B", "KB", "MB", "GB"]:
            if abs(size_bytes) < 1024:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024
        return f"{size_bytes:.1f} TB"
