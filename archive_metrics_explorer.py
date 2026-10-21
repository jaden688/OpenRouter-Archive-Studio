#!/usr/bin/env python3
"""Read-only SQLite metrics explorer for OpenRouter Archive Studio."""
import csv
import json
import pathlib
import sqlite3

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QCheckBox, QComboBox, QDialog, QFileDialog, QHBoxLayout, QHeaderView,
    QLabel, QLineEdit, QMessageBox, QPlainTextEdit, QPushButton,
    QScrollArea, QSplitter, QTableWidget, QTableWidgetItem, QVBoxLayout,
    QWidget
)

BASE = pathlib.Path(__file__).resolve().parent
PREFS = BASE / "metrics_layouts.json"
PAGE_SIZE = 150
DEFAULT_GENERATIONS = [
    "created_at_utc", "model", "provider_name", "tokens_prompt",
    "tokens_completion", "native_tokens_reasoning", "native_tokens_cached",
    "total_cost", "latency_ms", "generation_time_ms", "finish_reason",
    "request_id", "session_id"
]
USEFUL = [
    "request_count", "tokens_total", "tokens_prompt", "tokens_completion",
    "reasoning_tokens", "cached_tokens", "total_usage", "credits_usage",
    "avg_latency", "p95_latency", "avg_generation_time", "avg_router_latency"
]


def quoted(name):
    return '"' + name.replace('"', '""') + '"'


def field_text(value):
    if value is None:
        return ""
    if isinstance(value, bytes):
        return "<binary data: " + str(len(value)) + " bytes>"
    return str(value)


class ColumnPicker(QDialog):
    def __init__(self, available, checked, parent=None):
        super().__init__(parent)
        self.setWindowTitle("CHOOSE VISIBLE METRICS")
        self.resize(540, 660)
        lay = QVBoxLayout(self)
        lay.addWidget(QLabel("Select the columns to show. Drag column headers later to rearrange them."))
        self.find = QLineEdit()
        self.find.setPlaceholderText("Filter field names ...")
        lay.addWidget(self.find)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        host = QWidget()
        self.box = QVBoxLayout(host)
        self.checks = {}
        for name in available:
            check = QCheckBox(name)
            check.setChecked(name in checked)
            self.box.addWidget(check)
            self.checks[name] = check
        self.box.addStretch()
        scroll.setWidget(host)
        lay.addWidget(scroll)
        buttons = QHBoxLayout()
        for title, fn in (
            ("ALL", lambda: self.tick_all(True)),
            ("NONE", lambda: self.tick_all(False)),
            ("CANCEL", self.reject),
            ("APPLY", self.apply)
        ):
            b = QPushButton(title)
            b.clicked.connect(fn)
            buttons.addWidget(b)
        lay.addLayout(buttons)
        self.find.textChanged.connect(self.filter_checks)
        self.chosen = list(checked)

    def filter_checks(self, term):
        for name, cb in self.checks.items():
            cb.setVisible(term.lower() in name.lower())

    def tick_all(self, flag):
        for cb in self.checks.values():
            cb.setChecked(flag)

    def apply(self):
        self.chosen = [name for name, cb in self.checks.items() if cb.isChecked()]
        if not self.chosen:
            QMessageBox.warning(self, "No metrics", "Select at least one column.")
            return
        self.accept()


class FieldInspector(QDialog):
    def __init__(self, con, table, rowid, fields, parent=None):
        super().__init__(parent)
        self.con = con
        self.table = table
        self.rowid = rowid
        self.setWindowTitle("FULL RECORD / " + table)
        self.resize(1050, 760)
        lay = QVBoxLayout(self)
        lay.addWidget(QLabel("Original SQLite values • read-only • select a field to inspect its full contents"))
        top = QHBoxLayout()
        self.pick = QComboBox()
        self.pick.addItems(fields)
        top.addWidget(self.pick, 1)
        self.copy = QPushButton("COPY FIELD")
        top.addWidget(self.copy)
        lay.addLayout(top)
        self.value = QPlainTextEdit()
        self.value.setReadOnly(True)
        lay.addWidget(self.value)
        self.pick.currentTextChanged.connect(self.show_field)
        self.copy.clicked.connect(lambda: __import__("PySide6.QtWidgets", fromlist=["QApplication"]).QApplication.clipboard().setText(self.value.toPlainText()))
        self.show_field(self.pick.currentText())

    def show_field(self, name):
        if not name:
            return
        try:
            value = self.con.execute(
                "SELECT " + quoted(name) + " FROM " + quoted(self.table) +
                " WHERE rowid=?", (self.rowid,)
            ).fetchone()
            raw = value[0] if value else None
            out = field_text(raw)
            if isinstance(raw, str) and raw[:1] in ("{", "["):
                try:
                    out = json.dumps(json.loads(raw), indent=2, ensure_ascii=False)
                except (ValueError, TypeError):
                    pass
            self.value.setPlainText(out)
        except Exception as exc:
            self.value.setPlainText("Unable to read field: " + str(exc))


class MetricsExplorer(QDialog):
    def __init__(self, database, parent=None):
        super().__init__(parent)
        self.setWindowTitle("JL // SQLITE METRICS EXPLORER")
        self.resize(1480, 870)
        path = pathlib.Path(database).resolve()
        self.con = sqlite3.connect(path.as_uri() + "?mode=ro", uri=True, timeout=10)
        self.con.execute("PRAGMA query_only = ON")
        self.settings = self.read_settings()
        self.fields = []
        self.columns = []
        self.rowids = []
        self.page_rows = []
        self.page = 0
        self.total = 0
        self.order_by = None
        self.descending = True
        self.query = ""
        self.table_name = ""
        outer = QVBoxLayout(self)
        outer.addWidget(QLabel("◈ DATABASE METRICS  /  SELECT DATASET • CHOOSE FIELDS • INSPECT FULL RECORDS"))
        controls = QHBoxLayout()
        self.dataset = QComboBox()
        tables = [
            row[0] for row in self.con.execute(
                "SELECT name FROM sqlite_master WHERE type='table' "
                "AND name NOT LIKE 'sqlite_%' ORDER BY name"
            ) if row[0] != "source_account_auth_key"
        ]
        if "generations" in tables:
            tables.remove("generations")
            tables.insert(0, "generations")
        self.dataset.addItems(tables)
        controls.addWidget(self.dataset, 2)
        self.columns_button = QPushButton("☷ PICK COLUMNS")
        controls.addWidget(self.columns_button)
        self.reset_button = QPushButton("DEFAULT")
        controls.addWidget(self.reset_button)
        self.export_button = QPushButton("EXPORT PAGE CSV")
        controls.addWidget(self.export_button)
        outer.addLayout(controls)
        searching = QHBoxLayout()
        self.search = QLineEdit()
        self.search.setPlaceholderText("Search IDs, models, providers, or dataset labels • Enter to apply")
        searching.addWidget(self.search, 4)
        self.search_button = QPushButton("SEARCH")
        searching.addWidget(self.search_button)
        self.clear_button = QPushButton("CLEAR")
        searching.addWidget(self.clear_button)
        outer.addLayout(searching)
        self.status = QLabel("")
        outer.addWidget(self.status)
        self.grid = QTableWidget()
        self.grid.setEditTriggers(QTableWidget.NoEditTriggers)
        self.grid.setSelectionBehavior(QTableWidget.SelectRows)
        self.grid.horizontalHeader().setSectionsMovable(True)
        self.grid.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        self.grid.setWordWrap(False)
        outer.addWidget(self.grid, 1)
        nav = QHBoxLayout()
        self.prev = QPushButton("◀ PREVIOUS")
        nav.addWidget(self.prev)
        self.position = QLabel("")
        nav.addWidget(self.position, 1)
        self.next = QPushButton("NEXT ▶")
        nav.addWidget(self.next)
        self.detail = QPushButton("INSPECT SELECTED ROW")
        nav.addWidget(self.detail)
        outer.addLayout(nav)
        outer.addWidget(QLabel("Double-click a row to see every original field in full. Source tables are never edited."))
        self.dataset.currentTextChanged.connect(self.change_dataset)
        self.columns_button.clicked.connect(self.choose_columns)
        self.reset_button.clicked.connect(self.reset_layout)
        self.export_button.clicked.connect(self.export_page)
        self.search_button.clicked.connect(self.search_now)
        self.search.returnPressed.connect(self.search_now)
        self.clear_button.clicked.connect(self.clear_search)
        self.prev.clicked.connect(lambda: self.turn_page(-1))
        self.next.clicked.connect(lambda: self.turn_page(1))
        self.detail.clicked.connect(self.open_record)
        self.grid.cellDoubleClicked.connect(lambda row, col: self.open_record(row))
        self.grid.verticalScrollBar().valueChanged.connect(self.update_position)
        self.grid.horizontalHeader().sectionClicked.connect(self.sort_column)
        if tables:
            self.change_dataset(tables[0])

    @staticmethod
    def read_settings():
        try:
            data = json.loads(PREFS.read_text())
            return data if isinstance(data, dict) else {}
        except (OSError, ValueError):
            return {}

    def save_settings(self):
        try:
            tmp = PREFS.with_suffix(".json.tmp")
            tmp.write_text(json.dumps(self.settings, ensure_ascii=False, indent=2))
            tmp.replace(PREFS)
        except OSError as exc:
            QMessageBox.warning(self, "Layout not saved", str(exc))

    def recommended(self):
        if self.table_name == "generations":
            return [c for c in DEFAULT_GENERATIONS if c in self.fields]
        # First few grouping columns followed by actual metrics.
        groups = self.fields[:2]
        return list(dict.fromkeys(groups + [c for c in USEFUL if c in self.fields]))[:14] or self.fields[:8]

    def change_dataset(self, name):
        if not name:
            return
        self.table_name = name
        self.fields = [
            col[1] for col in self.con.execute("PRAGMA table_info(" + quoted(name) + ")")
        ]
        saved = self.settings.get(name, [])
        self.columns = [c for c in saved if c in self.fields] or self.recommended()
        self.page = 0
        self.order_by = "created_at_utc" if "created_at_utc" in self.fields else None
        self.descending = True
        self.search.setText("")
        self.query = ""
        self.reload()

    def choose_columns(self):
        picker = ColumnPicker(self.fields, self.columns, self)
        if picker.exec() == QDialog.Accepted:
            self.columns = picker.chosen
            self.settings[self.table_name] = list(self.columns)
            self.save_settings()
            self.page = 0
            self.reload()

    def reset_layout(self):
        self.columns = self.recommended()
        self.settings.pop(self.table_name, None)
        self.save_settings()
        self.page = 0
        self.reload()

    def search_now(self):
        self.query = self.search.text().strip()
        self.page = 0
        self.reload()

    def clear_search(self):
        self.search.clear()
        self.query = ""
        self.page = 0
        self.reload()

    def where_clause(self):
        if not self.query:
            return "", []
        if self.table_name == "generations":
            searchable = [c for c in ("id", "model", "provider_name", "request_id", "session_id", "finish_reason") if c in self.fields]
        else:
            searchable = [c for c in self.fields if c in (
                "model", "provider", "app", "finish_reason", "origin",
                "created_at__day", "created_at__week", "created_at__month",
                "created_at__hour", "name", "country", "api_key_id", "key"
            )]
            if not searchable:
                searchable = self.fields[:2]
        where = " WHERE (" + " OR ".join(
            "CAST(" + quoted(c) + " AS TEXT) LIKE ?" for c in searchable
        ) + ")"
        return where, ["%" + self.query + "%"] * len(searchable)

    def reload(self):
        if not self.columns:
            return
        try:
            where, params = self.where_clause()
            source = " FROM " + quoted(self.table_name) + where
            self.total = self.con.execute(
                "SELECT COUNT(*)" + source, params
            ).fetchone()[0]
            last_page = max(0, (self.total - 1) // PAGE_SIZE)
            self.page = min(self.page, last_page)
            # Show compact text previews in the table; full values remain in the record inspector.
            expr = ["rowid"] + [
                "CASE WHEN typeof(" + quoted(c) + ") IN ('text','blob') "
                "THEN substr(" + quoted(c) + ",1,300) ELSE " + quoted(c) +
                " END" for c in self.columns
            ]
            order = " ORDER BY " + quoted(self.order_by) + (" DESC" if self.descending else " ASC") if self.order_by else " ORDER BY rowid DESC"
            sql = "SELECT " + ", ".join(expr) + source + order + " LIMIT ? OFFSET ?"
            rows = self.con.execute(sql, params + [PAGE_SIZE, self.page * PAGE_SIZE]).fetchall()
        except sqlite3.Error as exc:
            self.status.setText("DATABASE QUERY ERROR: " + str(exc))
            return
        self.rowids = [r[0] for r in rows]
        self.page_rows = [r[1:] for r in rows]
        self.grid.setUpdatesEnabled(False)
        self.grid.setRowCount(len(rows))
        self.grid.setColumnCount(len(self.columns))
        self.grid.setHorizontalHeaderLabels(self.columns)
        # Row headers are GLOBAL record positions, not 1–150 repeated on each page.
        self.grid.setVerticalHeaderLabels(
            [f"{self.page * PAGE_SIZE + i + 1:,}" for i in range(len(rows))]
        )
        self.grid.clearSelection()
        for i, row in enumerate(self.page_rows):
            for j, value in enumerate(row):
                item = QTableWidgetItem(field_text(value))
                item.setToolTip(self.columns[j] + " (double-click row for full value)")
                self.grid.setItem(i, j, item)
        self.grid.setUpdatesEnabled(True)
        self.grid.resizeColumnsToContents()
        for j in range(len(self.columns)):
            if self.grid.columnWidth(j) > 280:
                self.grid.setColumnWidth(j, 280)
        # Navigation always starts at the first row of the newly loaded page.
        self.grid.verticalScrollBar().setValue(0)
        self.update_position()
        hi = self.page * PAGE_SIZE + len(rows)
        self.status.setText(self.table_name + "  •  " + str(len(self.fields)) + " available metrics  •  " +
                            str(len(self.columns)) + " visible  •  " + format(self.total, ",") + " matching records")
        self.prev.setEnabled(self.page > 0)
        self.next.setEnabled(hi < self.total)

    def update_position(self, *_):
        """Keep page and first-visible-row numbers in sync while scrolling."""
        count = max(1, (self.total + PAGE_SIZE - 1) // PAGE_SIZE)
        first = self.page * PAGE_SIZE + 1 if self.page_rows else 0
        last = self.page * PAGE_SIZE + len(self.page_rows)
        top = self.grid.rowAt(0)
        visible = self.page * PAGE_SIZE + max(0, top) + 1 if self.page_rows else 0
        self.position.setText(
            f"PAGE {self.page + 1:,} / {count:,}  •  ROWS {first:,}–{last:,} / {self.total:,}  •  TOP ROW {visible:,}"
        )

    def turn_page(self, amount):
        self.page = max(0, self.page + amount)
        self.reload()

    def sort_column(self, index):
        if index < 0 or index >= len(self.columns):
            return
        chosen = self.columns[index]
        if self.order_by == chosen:
            self.descending = not self.descending
        else:
            self.order_by = chosen
            self.descending = True
        self.page = 0
        self.reload()

    def open_record(self, row=None):
        if row is None:
            row = self.grid.currentRow()
        if row < 0 or row >= len(self.rowids):
            return
        dlg = FieldInspector(self.con, self.table_name, self.rowids[row], self.fields, self)
        dlg.exec()

    def export_page(self):
        if not self.page_rows:
            return
        target, _ = QFileDialog.getSaveFileName(
            self, "Export visible page", str(pathlib.Path.home() / (self.table_name + "-page.csv")),
            "CSV (*.csv)"
        )
        if not target:
            return
        try:
            with open(target, "w", newline="", encoding="utf-8") as out:
                writer = csv.writer(out)
                writer.writerow(self.columns)
                for row in self.page_rows:
                    writer.writerow([field_text(value) for value in row])
            QMessageBox.information(self, "Export complete", "Exported the visible page with selected columns. Text fields use 300-character previews.")
        except OSError as exc:
            QMessageBox.warning(self, "Export failed", str(exc))

    def closeEvent(self, event):
        self.con.close()
        super().closeEvent(event)
