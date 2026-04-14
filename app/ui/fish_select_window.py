"""Fish selection window UI."""

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

from app.services import fish_select_logic


class FishSelectWindow(QMainWindow):
    """Window that displays fish list and details."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Fish Select")
        self.setMinimumSize(700, 420)

        container = QWidget(self)
        layout = QVBoxLayout(container)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(12)

        header = QLabel("Fish Selection", container)
        header.setAlignment(Qt.AlignLeft)
        header.setStyleSheet("font-size: 20px; font-weight: 700; color: #E8F0FF;")

        self._table = QTableWidget(container)
        self._table.setColumnCount(2)
        self._table.setHorizontalHeaderLabels(["ID", "Name"])
        self._table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self._table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self._table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self._table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self._table.setSelectionMode(QAbstractItemView.SingleSelection)
        self._table.itemSelectionChanged.connect(self._update_details)

        self._details = QLabel("Select a fish to view details.", container)
        self._details.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        self._details.setStyleSheet("font-size: 13px; font-weight: 500; color: #C9D7F2;")
        self._details.setWordWrap(True)

        close_button = QPushButton("Close", container)
        close_button.setFixedHeight(32)
        close_button.clicked.connect(self.close)

        layout.addWidget(header)
        layout.addWidget(self._table)
        layout.addWidget(self._details)
        layout.addWidget(close_button, alignment=Qt.AlignRight)

        self.setCentralWidget(container)
        self._load_fish_list()

    def _load_fish_list(self) -> None:
        rows = fish_select_logic.get_fish_list()
        self._table.setRowCount(len(rows))

        for row_index, (fish_id, name) in enumerate(rows):
            self._table.setItem(row_index, 0, QTableWidgetItem(str(fish_id)))
            self._table.setItem(row_index, 1, QTableWidgetItem(name))

        if rows:
            self._table.selectRow(0)
            self._update_details()

    def _update_details(self) -> None:
        items = self._table.selectedItems()
        if not items:
            self._details.setText("Select a fish to view details.")
            return

        fish_id = int(items[0].text())
        fish = fish_select_logic.get_fish_by_id(fish_id)
        if not fish:
            self._details.setText("No details found for this fish.")
            return

        text = (
            f"Name: {fish['name']}\n"
            f"Behavior: {fish['behavior']}\n"
            f"Size: {fish['size']}\n"
            f"Temperature: {fish['temperature']}\n"
            f"pH: {fish['ph']}"
        )
        self._details.setText(text)
