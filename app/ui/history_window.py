"""History window UI."""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QAbstractItemView,
    QHeaderView,
    QLabel,
    QMainWindow,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from app.services import fish_list


class HistoryWindow(QMainWindow):
    """Window that displays compatibility history entries."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("History")
        self.setMinimumSize(820, 420)

        container = QWidget(self)
        layout = QVBoxLayout(container)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(12)

        header = QLabel("Compatibility History", container)
        header.setAlignment(Qt.AlignLeft)
        header.setStyleSheet("font-size: 20px; font-weight: 700; color: #E8F0FF;")

        self._table = QTableWidget(container)
        self._table.setColumnCount(5)
        self._table.setHorizontalHeaderLabels(["ID", "Timestamp", "Aquarium", "Fish", "Result"])
        self._table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self._table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self._table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self._table.horizontalHeader().setSectionResizeMode(3, QHeaderView.Stretch)
        self._table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeToContents)
        self._table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self._table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self._table.setSelectionMode(QAbstractItemView.SingleSelection)

        self._status = QLabel("Select an entry to delete.", container)
        self._status.setAlignment(Qt.AlignLeft)
        self._status.setStyleSheet("font-size: 12px; color: #C9D7F2;")

        delete_button = QPushButton("Delete Selected", container)
        delete_button.setFixedHeight(32)
        delete_button.clicked.connect(self._delete_selected)

        close_button = QPushButton("Close", container)
        close_button.setFixedHeight(32)
        close_button.clicked.connect(self.close)

        layout.addWidget(header)
        layout.addWidget(self._table)
        layout.addWidget(self._status)
        layout.addWidget(delete_button, alignment=Qt.AlignRight)
        layout.addWidget(close_button, alignment=Qt.AlignRight)

        self.setCentralWidget(container)
        self._load_history()

    def _load_history(self) -> None:
        rows = fish_list.get_history_entries()
        self._table.setRowCount(len(rows))

        for row_index, (entry_id, timestamp, aquarium_name, fish_names, result) in enumerate(rows):
            self._table.setItem(row_index, 0, QTableWidgetItem(str(entry_id)))
            self._table.setItem(row_index, 1, QTableWidgetItem(timestamp))
            self._table.setItem(row_index, 2, QTableWidgetItem(aquarium_name or "-"))
            self._table.setItem(row_index, 3, QTableWidgetItem(fish_names))
            self._table.setItem(row_index, 4, QTableWidgetItem(result))

        if not rows:
            self._status.setText("No history entries found.")
        else:
            self._status.setText("Select an entry to delete.")

    def _delete_selected(self) -> None:
        items = self._table.selectedItems()
        if not items:
            self._status.setText("Select an entry to delete.")
            return

        entry_id = int(items[0].text())
        if fish_list.delete_history_entry_db(entry_id):
            self._status.setText("Entry deleted.")
        else:
            self._status.setText("Entry not found.")

        self._load_history()
