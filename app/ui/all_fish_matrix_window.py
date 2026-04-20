"""Window for displaying the compatibility matrix for all fish."""

from __future__ import annotations

import sys
from pathlib import Path

from PySide6.QtCore import QAbstractTableModel, QModelIndex, QObject, QThread, Qt, QTimer, Signal
from PySide6.QtGui import QColor, QBrush
from PySide6.QtWidgets import (
    QApplication,
    QAbstractItemView,
    QHeaderView,
    QLabel,
    QTableView,
    QVBoxLayout,
    QWidget,
)

try:
    from app.database.db_setup import create_tables
    from app.services.fish_pair_logic import (
        STATUS_GREEN,
        STATUS_RED,
        STATUS_SELF,
        STATUS_YELLOW,
        build_compatibility_matrix,
    )
except ModuleNotFoundError:
    sys.path.append(str(Path(__file__).resolve().parents[2]))
    from app.database.db_setup import create_tables
    from app.services.fish_pair_logic import (
        STATUS_GREEN,
        STATUS_RED,
        STATUS_SELF,
        STATUS_YELLOW,
        build_compatibility_matrix,
    )


class MatrixLoader(QObject):
    """Loads the matrix off the UI thread."""

    finished = Signal(dict)
    failed = Signal(str)

    def run(self) -> None:
        try:
            self.finished.emit(build_compatibility_matrix())
        except Exception as exc:  # pragma: no cover
            self.failed.emit(str(exc))


class FishMatrixTableModel(QAbstractTableModel):
    """Virtualized model for a very large compatibility matrix."""

    def __init__(self, fish_names: list[str], matrix: list[bytearray], parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._fish_names = fish_names
        self._matrix = matrix
        self._wrapped_columns = [self._wrap_header_text(name) for name in fish_names]
        self._status_labels = {
            STATUS_SELF: "",
            STATUS_GREEN: "G",
            STATUS_YELLOW: "Y",
            STATUS_RED: "R",
        }
        self._tooltips = {
            STATUS_SELF: "Same fish",
            STATUS_GREEN: "GREEN",
            STATUS_YELLOW: "YELLOW",
            STATUS_RED: "RED",
        }
        self._backgrounds = {
            STATUS_SELF: QBrush(QColor("#93C5FD")),
            STATUS_GREEN: QBrush(QColor("#22C55E")),
            STATUS_YELLOW: QBrush(QColor("#FACC15")),
            STATUS_RED: QBrush(QColor("#EF4444")),
        }
        self._foregrounds = {
            STATUS_SELF: QBrush(QColor("#111827")),
            STATUS_GREEN: QBrush(QColor("#FFFFFF")),
            STATUS_YELLOW: QBrush(QColor("#111827")),
            STATUS_RED: QBrush(QColor("#FFFFFF")),
        }

    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:  # noqa: N802
        if parent.isValid():
            return 0
        return len(self._fish_names)

    def columnCount(self, parent: QModelIndex = QModelIndex()) -> int:  # noqa: N802
        if parent.isValid():
            return 0
        return len(self._fish_names)

    def data(self, index: QModelIndex, role: int = Qt.DisplayRole):  # noqa: ANN201
        if not index.isValid():
            return None

        status = self._matrix[index.row()][index.column()]

        if role == Qt.DisplayRole:
            return self._status_labels.get(status, "")
        if role == Qt.TextAlignmentRole:
            return int(Qt.AlignCenter)
        if role == Qt.BackgroundRole:
            return self._backgrounds.get(status)
        if role == Qt.ForegroundRole:
            return self._foregrounds.get(status)
        if role == Qt.ToolTipRole:
            return self._tooltips.get(status, "")
        return None

    def headerData(self, section: int, orientation: Qt.Orientation, role: int = Qt.DisplayRole):  # noqa: ANN201,N802
        if role == Qt.DisplayRole:
            if orientation == Qt.Horizontal:
                return self._wrapped_columns[section]
            return self._fish_names[section]
        if role == Qt.TextAlignmentRole:
            return int(Qt.AlignCenter if orientation == Qt.Horizontal else Qt.AlignVCenter | Qt.AlignLeft)
        return None

    @staticmethod
    def _wrap_header_text(value: str, chunk_size: int = 12) -> str:
        words = value.split()
        if len(value) <= chunk_size or len(words) <= 1:
            return value

        lines: list[str] = []
        current_line = words[0]
        for word in words[1:]:
            candidate = f"{current_line} {word}"
            if len(candidate) <= chunk_size:
                current_line = candidate
            else:
                lines.append(current_line)
                current_line = word
        lines.append(current_line)
        return "\n".join(lines)


class AllFishMatrixWindow(QWidget):
    """A lightweight window that renders the full fish compatibility matrix."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(None)
        create_tables()

        self._matrix_loaded = False
        self._matrix_loading = False
        self._loader_thread: QThread | None = None
        self._loader: MatrixLoader | None = None
        self._table_model: FishMatrixTableModel | None = None

        self.setWindowTitle("Proprif Fish - All Fish Matrix")
        self.setMinimumSize(980, 720)
        self.setWindowFlag(Qt.Window, True)
        self.setStyleSheet("color: #111827; background-color: #FFFFFF;")

        self._build_ui()
        QTimer.singleShot(0, self._ensure_matrix_loaded)

    def showEvent(self, event) -> None:  # type: ignore[override]
        super().showEvent(event)
        if not self._matrix_loaded and not self._matrix_loading:
            QTimer.singleShot(0, self._ensure_matrix_loaded)

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        title = QLabel("All Fish Matrix", self)
        title.setStyleSheet("font-size: 24px; font-weight: 700; color: #1F4E79;")

        self.subtitle = QLabel("Opening matrix window...", self)
        self.subtitle.setWordWrap(True)
        self.subtitle.setStyleSheet("font-size: 14px; color: #4A5568;")

        self.matrix_table = QTableView(self)
        self.matrix_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.matrix_table.setSelectionMode(QAbstractItemView.NoSelection)
        self.matrix_table.setFocusPolicy(Qt.NoFocus)
        self.matrix_table.setAlternatingRowColors(False)
        self.matrix_table.setWordWrap(True)
        self.matrix_table.setTextElideMode(Qt.ElideNone)
        self.matrix_table.horizontalHeader().setSectionResizeMode(QHeaderView.Fixed)
        self.matrix_table.verticalHeader().setSectionResizeMode(QHeaderView.Fixed)
        self.matrix_table.horizontalHeader().setDefaultSectionSize(124)
        self.matrix_table.horizontalHeader().setMinimumSectionSize(96)
        self.matrix_table.horizontalHeader().setFixedHeight(56)
        self.matrix_table.verticalHeader().setDefaultSectionSize(28)
        self.matrix_table.verticalHeader().setMinimumWidth(180)
        self.matrix_table.setHorizontalScrollMode(QAbstractItemView.ScrollPerPixel)
        self.matrix_table.setVerticalScrollMode(QAbstractItemView.ScrollPerPixel)
        self.matrix_table.setStyleSheet(
            "color: #111827; background-color: white; font-size: 11px; gridline-color: #D1D5DB;"
            "QHeaderView::section { font-size: 11px; padding: 6px 8px; font-weight: 600; }"
        )

        layout.addWidget(title)
        layout.addWidget(self.subtitle)
        layout.addWidget(self.matrix_table, stretch=1)

    def _ensure_matrix_loaded(self) -> None:
        if self._matrix_loaded or self._matrix_loading:
            return

        self._matrix_loading = True
        self.subtitle.setText("Loading the fish compatibility matrix in background...")

        self._loader_thread = QThread(self)
        self._loader = MatrixLoader()
        self._loader.moveToThread(self._loader_thread)
        self._loader_thread.started.connect(self._loader.run)
        self._loader.finished.connect(self._handle_matrix_loaded)
        self._loader.failed.connect(self._handle_matrix_failed)
        self._loader.finished.connect(self._loader_thread.quit)
        self._loader.failed.connect(self._loader_thread.quit)
        self._loader_thread.finished.connect(self._cleanup_loader)
        self._loader_thread.start()

    def _handle_matrix_loaded(self, matrix_data: dict) -> None:
        fish_names = matrix_data["fish"]
        matrix = matrix_data["matrix"]
        self._table_model = FishMatrixTableModel(fish_names, matrix, self.matrix_table)
        self.matrix_table.setModel(self._table_model)
        self.subtitle.setText(
            f"Loaded {len(fish_names)} fish. Green means compatible, yellow means caution, red means incompatible."
        )
        self._matrix_loaded = True
        self._matrix_loading = False

    def _handle_matrix_failed(self, message: str) -> None:
        self.subtitle.setText(f"Failed to load matrix: {message}")
        self._matrix_loading = False

    def _cleanup_loader(self) -> None:
        if self._loader is not None:
            self._loader.deleteLater()
            self._loader = None
        if self._loader_thread is not None:
            self._loader_thread.deleteLater()
            self._loader_thread = None


if __name__ == "__main__":
    app = QApplication([])
    window = AllFishMatrixWindow()
    window.show()
    app.exec()
