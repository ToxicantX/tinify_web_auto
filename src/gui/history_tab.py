from datetime import datetime, timedelta
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                                QTableWidget, QTableWidgetItem, QHeaderView,
                                QLineEdit, QMenu, QAbstractItemView, QLabel,
                                QDateEdit, QMessageBox)
from PySide6.QtCore import Qt, QDate

from src.data import database
from src.gui.widgets.compare_dialog import CompareDialog


class HistoryTab(QWidget):

    def __init__(self, parent=None):
        super().__init__(parent)
        self._page = 1
        self._page_size = 50
        self._init_ui()
        self._load_data()

    def _init_ui(self):
        layout = QVBoxLayout(self)

        # Search bar
        search_layout = QHBoxLayout()

        self._search_input = QLineEdit()
        self._search_input.setPlaceholderText("搜索文件名...")
        self._search_input.setFixedWidth(200)
        self._search_input.returnPressed.connect(self._on_search)

        search_btn = QPushButton("搜索")
        search_btn.clicked.connect(self._on_search)

        date_label = QLabel("日期:")
        self._date_from = QDateEdit(QDate.currentDate().addMonths(-1))
        self._date_from.setCalendarPopup(True)
        self._date_from.setFixedWidth(120)
        self._date_to = QDateEdit(QDate.currentDate())
        self._date_to.setCalendarPopup(True)
        self._date_to.setFixedWidth(120)

        clear_btn = QPushButton("清除筛选")
        clear_btn.clicked.connect(self._on_clear_filter)

        search_layout.addWidget(self._search_input)
        search_layout.addWidget(search_btn)
        search_layout.addWidget(date_label)
        search_layout.addWidget(self._date_from)
        search_layout.addWidget(self._date_to)
        search_layout.addWidget(clear_btn)
        search_layout.addStretch()

        layout.addLayout(search_layout)

        # Table
        self._table = QTableWidget(0, 7)
        self._table.setHorizontalHeaderLabels([
            "文件名", "原始大小", "压缩后", "压缩率", "耗时", "模式", "时间"
        ])
        self._table.horizontalHeader().setStretchLastSection(True)
        self._table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self._table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self._table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self._table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self._table.customContextMenuRequested.connect(self._on_context_menu)
        layout.addWidget(self._table)

        # Stats bar
        stats_layout = QHBoxLayout()
        self._stats_label = QLabel("")
        self._stats_label.setStyleSheet("color: #666;")
        stats_layout.addWidget(self._stats_label)
        stats_layout.addStretch()

        prev_btn = QPushButton("上一页")
        prev_btn.clicked.connect(self._prev_page)
        next_btn = QPushButton("下一页")
        next_btn.clicked.connect(self._next_page)
        self._page_label = QLabel("")

        stats_layout.addWidget(prev_btn)
        stats_layout.addWidget(self._page_label)
        stats_layout.addWidget(next_btn)
        layout.addLayout(stats_layout)

    def _load_data(self):
        keyword = self._search_input.text().strip() or None
        date_from = self._date_from.date().toString("yyyy-MM-dd") if self._date_from.date() != QDate(2000, 1, 1) else None
        date_to = self._date_to.date().toString("yyyy-MM-dd")

        records, total = database.get_records(
            self._page, self._page_size, keyword, date_from, date_to
        )

        self._table.setRowCount(len(records))
        for i, r in enumerate(records):
            self._table.setItem(i, 0, QTableWidgetItem(r["original_name"]))
            self._table.setItem(i, 1, QTableWidgetItem(self._fmt_size(r["original_size"])))
            self._table.setItem(i, 2, QTableWidgetItem(self._fmt_size(r["compressed_size"])))
            self._table.setItem(i, 3, QTableWidgetItem(f"{r['ratio']:.1f}%"))
            self._table.setItem(i, 4, QTableWidgetItem(f"{r['duration_ms'] / 1000:.1f}s"))
            mode_text = "API" if r["mode"] == "api" else "网页"
            self._table.setItem(i, 5, QTableWidgetItem(mode_text))
            self._table.setItem(i, 6, QTableWidgetItem(r["created_at"] or ""))

            # Color the ratio
            if r["ratio"] > 50:
                self._table.item(i, 3).setForeground(Qt.GlobalColor.green)

        # Store record IDs for context menu
        self._record_ids = [r["id"] for r in records]
        self._record_paths = [(r["original_path"], r["output_path"]) for r in records]

        total_pages = max(1, (total + self._page_size - 1) // self._page_size)
        self._page_label.setText(f"第 {self._page}/{total_pages} 页 (共 {total} 条)")

        # Update stats
        stats = database.get_total_stats()
        if stats["count"] > 0:
            orig = self._fmt_size(stats["total_orig"])
            comp = self._fmt_size(stats["total_comp"])
            saved_pct = round((1 - stats["total_comp"] / stats["total_orig"]) * 100, 1) if stats["total_orig"] > 0 else 0
            self._stats_label.setText(f"总计: {stats['count']} 个文件 | 原始 {orig} -> 压缩 {comp} | 节省 {saved_pct}%")

    def _on_search(self):
        self._page = 1
        self._load_data()

    def _on_clear_filter(self):
        self._search_input.clear()
        self._date_from.setDate(QDate(2000, 1, 1))
        self._date_to.setDate(QDate.currentDate())
        self._page = 1
        self._load_data()

    def _prev_page(self):
        if self._page > 1:
            self._page -= 1
            self._load_data()

    def _next_page(self):
        self._page += 1
        self._load_data()

    def _on_context_menu(self, pos):
        row = self._table.currentRow()
        if row < 0 or row >= len(self._record_paths):
            return

        menu = QMenu(self)
        orig_path, comp_path = self._record_paths[row]

        compare_action = menu.addAction("查看压缩对比")
        open_orig_action = menu.addAction("打开原始文件位置")
        open_comp_action = menu.addAction("打开压缩文件位置")
        menu.addSeparator()
        delete_action = menu.addAction("删除记录")

        action = menu.exec(self._table.viewport().mapToGlobal(pos))

        import os, subprocess
        if action == compare_action:
            if os.path.exists(orig_path) and os.path.exists(comp_path):
                dlg = CompareDialog(orig_path, comp_path, self)
                dlg.exec()
            else:
                QMessageBox.warning(self, "提示", "原始文件或压缩文件已不存在")
        elif action == open_orig_action:
            if os.path.exists(orig_path):
                subprocess.Popen(f'explorer /select,"{os.path.normpath(orig_path)}"')
        elif action == open_comp_action:
            if os.path.exists(comp_path):
                subprocess.Popen(f'explorer /select,"{os.path.normpath(comp_path)}"')
        elif action == delete_action:
            record_id = self._record_ids[row]
            database.delete_records([record_id])
            self._load_data()

    def refresh(self):
        self._load_data()

    @staticmethod
    def _fmt_size(size_bytes: int) -> str:
        for unit in ["B", "KB", "MB", "GB"]:
            if abs(size_bytes) < 1024:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024
        return f"{size_bytes:.1f} TB"
