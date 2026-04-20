"""Fish comparison UI for selecting, comparing, and adding fish to aquariums."""

from __future__ import annotations

import sys
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QApplication,
    QAbstractItemView,
    QComboBox,
    QGridLayout,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

try:
    from app.database.db_setup import create_tables
    from app.services.fish_comparison_logic import (
        MAX_FISH_TO_COMPARE,
        MIN_FISH_TO_COMPARE,
        FishComparisonError,
        get_comparison_view_model,
        search_fish_candidates,
    )
    from app.services.multiple_aquarium_logic import get_all_aquariums
    from app.services.search_and_add_fish import add_fish_to_aquarium
    from app.ui.all_fish_matrix_window import AllFishMatrixWindow
    from app.ui.aquarium_management_page import AquariumManagementPage
except ModuleNotFoundError:
    sys.path.append(str(Path(__file__).resolve().parents[2]))
    from app.database.db_setup import create_tables
    from app.services.fish_comparison_logic import (
        MAX_FISH_TO_COMPARE,
        MIN_FISH_TO_COMPARE,
        FishComparisonError,
        get_comparison_view_model,
        search_fish_candidates,
    )
    from app.services.multiple_aquarium_logic import get_all_aquariums
    from app.services.search_and_add_fish import add_fish_to_aquarium
    from app.ui.all_fish_matrix_window import AllFishMatrixWindow
    from app.ui.aquarium_management_page import AquariumManagementPage


class FishComparisonPage(QWidget):
    """Window for comparing up to five fish before adding one to an aquarium."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        create_tables()

        self.selected_fish_ids: list[int] = []
        self.selected_fish_cards: dict[int, dict] = {}
        self.aquariums: list[dict] = []
        self.all_fish_matrix_window: AllFishMatrixWindow | None = None
        self.management_window: AquariumManagementPage | None = None

        self.setMinimumSize(1200, 760)
        self.setStyleSheet("color: #111827; background-color: #FFFFFF;")

        self._build_ui()
        self._load_aquariums()
        self._update_catalog()
        self._refresh_comparison()

    def _build_ui(self) -> None:
        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(24, 24, 24, 24)
        root_layout.setSpacing(16)

        header = QLabel("Fish Compatibility Comparison", self)
        header.setStyleSheet("font-size: 28px; font-weight: 700; color: #1F4E79;")

        subtitle = QLabel(
            "Select 2 to 5 fish, compare their key parameters in one view, "
            "and send one of them directly to an aquarium without leaving the page.",
            self,
        )
        subtitle.setWordWrap(True)
        subtitle.setStyleSheet("font-size: 14px; color: #4A5568;")

        root_layout.addWidget(header)
        root_layout.addWidget(subtitle)
        root_layout.addWidget(self._build_status_row())

        content_layout = QHBoxLayout()
        content_layout.setSpacing(18)
        content_layout.addWidget(self._build_selection_panel(), stretch=1)

        comparison_column = QVBoxLayout()
        comparison_column.setSpacing(18)
        comparison_column.addWidget(self._build_comparison_panel(), stretch=1)
        comparison_column.addWidget(self._build_action_panel())

        comparison_container = QWidget(self)
        comparison_container.setLayout(comparison_column)
        content_layout.addWidget(comparison_container, stretch=3)

        root_layout.addLayout(content_layout, stretch=1)

    def _build_status_row(self) -> QWidget:
        panel = QWidget(self)
        layout = QHBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)

        self.selection_badge = QLabel("Selected: 0/5", panel)
        self.selection_badge.setAlignment(Qt.AlignCenter)
        self.selection_badge.setMinimumWidth(140)
        self.selection_badge.setStyleSheet(self._badge_style("#1F4E79"))

        self.overall_badge = QLabel("Status: choose fish", panel)
        self.overall_badge.setAlignment(Qt.AlignCenter)
        self.overall_badge.setMinimumWidth(180)
        self.overall_badge.setStyleSheet(self._badge_style("#718096"))

        self.summary_label = QLabel(
            f"Select at least {MIN_FISH_TO_COMPARE} fish to generate the comparison.",
            panel,
        )
        self.summary_label.setWordWrap(True)
        self.summary_label.setStyleSheet("color: #4A5568;")

        layout.addWidget(self.selection_badge)
        layout.addWidget(self.overall_badge)
        layout.addWidget(self.summary_label, stretch=1)
        return panel

    def _build_selection_panel(self) -> QWidget:
        panel = QWidget(self)
        panel.setStyleSheet(self._panel_style())
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        title = QLabel("Fish Selection", panel)
        title.setStyleSheet("font-size: 20px; font-weight: 600; color: #234E52;")

        helper = QLabel(
            f"Search the catalog and build a comparison set of {MIN_FISH_TO_COMPARE}-{MAX_FISH_TO_COMPARE} fish.",
            panel,
        )
        helper.setWordWrap(True)
        helper.setStyleSheet("color: #4A5568;")

        self.search_input = QLineEdit(panel)
        self.search_input.setPlaceholderText("Search fish by name...")
        self.search_input.textChanged.connect(self._update_catalog)
        self.search_input.setStyleSheet("color: #111827; background-color: white;")

        self.catalog_list = QListWidget(panel)
        self.catalog_list.setStyleSheet("color: #111827; background-color: white;")
        self.catalog_list.itemDoubleClicked.connect(lambda _item: self._add_selected_candidate())

        self.add_candidate_button = QPushButton("Add To Comparison", panel)
        self.add_candidate_button.clicked.connect(self._add_selected_candidate)

        self.catalog_feedback_label = QLabel("", panel)
        self.catalog_feedback_label.setWordWrap(True)

        selected_title = QLabel("Selected Fish", panel)
        selected_title.setStyleSheet("font-size: 18px; font-weight: 600; color: #744210;")

        self.selected_list = QListWidget(panel)
        self.selected_list.setStyleSheet("color: #111827; background-color: white;")
        self.selected_list.itemDoubleClicked.connect(lambda _item: self._remove_selected_fish())

        selected_buttons = QHBoxLayout()
        self.remove_selected_button = QPushButton("Remove Selected", panel)
        self.remove_selected_button.clicked.connect(self._remove_selected_fish)
        self.clear_selection_button = QPushButton("Clear All", panel)
        self.clear_selection_button.clicked.connect(self._clear_selection)
        self.remove_selected_button.setEnabled(False)
        self.clear_selection_button.setEnabled(False)
        selected_buttons.addWidget(self.remove_selected_button)
        selected_buttons.addWidget(self.clear_selection_button)

        layout.addWidget(title)
        layout.addWidget(helper)
        layout.addWidget(self.search_input)
        layout.addWidget(self.catalog_list, stretch=1)
        layout.addWidget(self.add_candidate_button)
        layout.addWidget(self.catalog_feedback_label)
        layout.addSpacing(8)
        layout.addWidget(selected_title)
        layout.addWidget(self.selected_list, stretch=1)
        layout.addLayout(selected_buttons)
        return panel

    def _build_comparison_panel(self) -> QWidget:
        panel = QWidget(self)
        panel.setStyleSheet(self._panel_style())
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        title_row = QHBoxLayout()
        title_row.setContentsMargins(0, 0, 0, 0)
        title_row.setSpacing(12)

        title = QLabel("Comparison Overview", panel)
        title.setStyleSheet("font-size: 20px; font-weight: 600; color: #234E52;")

        self.open_all_fish_matrix_button = QPushButton("All fish matrix", panel)
        self.open_all_fish_matrix_button.clicked.connect(self._open_all_fish_matrix_window)
        self.open_all_fish_matrix_button.setCursor(Qt.PointingHandCursor)
        self.open_all_fish_matrix_button.setMinimumHeight(36)
        self.open_all_fish_matrix_button.setStyleSheet(
            "QPushButton {"
            "background-color: #1D4ED8; color: white; border: 1px solid #1E40AF; "
            "border-radius: 10px; padding: 8px 14px; font-weight: 600;"
            "}"
            "QPushButton:hover { background-color: #1E40AF; }"
            "QPushButton:pressed { background-color: #1E3A8A; }"
        )

        title_row.addWidget(title)
        title_row.addStretch(1)
        title_row.addWidget(self.open_all_fish_matrix_button)

        self.comparison_hint_label = QLabel(
            "The selected fish cards and their differences will appear here.",
            panel,
        )
        self.comparison_hint_label.setWordWrap(True)
        self.comparison_hint_label.setStyleSheet("color: #4A5568;")

        self.comparison_notes_label = QLabel(
            "Compatibility notes will appear here after you compare fish.",
            panel,
        )
        self.comparison_notes_label.setWordWrap(True)
        self.comparison_notes_label.setStyleSheet(
            "color: #2D3748; background-color: #FFFFFF; border: 1px solid #D6E4F0; "
            "border-radius: 12px; padding: 12px;"
        )
        self.comparison_notes_label.hide()

        self.cards_panel = QWidget(panel)
        self.cards_layout = QGridLayout(self.cards_panel)
        self.cards_layout.setContentsMargins(0, 0, 0, 0)
        self.cards_layout.setHorizontalSpacing(8)
        self.cards_layout.setVerticalSpacing(8)

        self.comparison_table = QTableWidget(panel)
        self.comparison_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.comparison_table.setSelectionMode(QAbstractItemView.NoSelection)
        self.comparison_table.setFocusPolicy(Qt.NoFocus)
        self.comparison_table.setWordWrap(True)
        self.comparison_table.setHorizontalScrollMode(QAbstractItemView.ScrollPerPixel)
        self.comparison_table.setVerticalScrollMode(QAbstractItemView.ScrollPerPixel)
        self.comparison_table.setTextElideMode(Qt.ElideNone)
        self.comparison_table.verticalHeader().setVisible(False)
        self.comparison_table.horizontalHeader().setStretchLastSection(False)
        self.comparison_table.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        self.comparison_table.setStyleSheet(
            "color: #111827; background-color: white; font-size: 11px;"
            "QHeaderView::section { font-size: 11px; padding: 4px 6px; }"
        )

        self.highlights_label = QLabel("No comparison highlights yet.", panel)
        self.highlights_label.setWordWrap(True)
        self.highlights_label.setStyleSheet("color: #2D3748;")

        layout.addLayout(title_row)
        layout.addWidget(self.comparison_hint_label)
        layout.addWidget(self.cards_panel)
        layout.addWidget(self.comparison_table, stretch=1)
        layout.addWidget(self.highlights_label)
        return panel

    def _build_action_panel(self) -> QWidget:
        panel = QWidget(self)
        panel.setStyleSheet(self._panel_style())
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        title = QLabel("Add Compared Fish To Aquarium", panel)
        title.setStyleSheet("font-size: 20px; font-weight: 600; color: #744210;")

        helper = QLabel(
            "After reviewing the comparison, pick one of the compared fish and add it to an aquarium.",
            panel,
        )
        helper.setWordWrap(True)
        helper.setStyleSheet("color: #4A5568;")

        controls = QHBoxLayout()
        controls.setSpacing(12)

        self.aquarium_selector = QComboBox(panel)
        self.aquarium_selector.setStyleSheet("color: #111827; background-color: white;")
        self.aquarium_selector.currentIndexChanged.connect(self._update_add_controls)
        controls.addWidget(self.aquarium_selector, stretch=2)

        self.add_fish_selector = QComboBox(panel)
        self.add_fish_selector.setStyleSheet("color: #111827; background-color: white;")
        self.add_fish_selector.currentIndexChanged.connect(self._update_add_controls)
        controls.addWidget(self.add_fish_selector, stretch=2)

        self.quantity_input = QSpinBox(panel)
        self.quantity_input.setRange(1, 999)
        self.quantity_input.setValue(1)
        self.quantity_input.setStyleSheet("color: #111827; background-color: white;")
        controls.addWidget(self.quantity_input)

        self.add_to_aquarium_button = QPushButton("Add To Aquarium", panel)
        self.add_to_aquarium_button.clicked.connect(self._handle_add_to_aquarium)
        self.add_to_aquarium_button.setEnabled(False)
        controls.addWidget(self.add_to_aquarium_button)

        footer = QHBoxLayout()
        self.feedback_label = QLabel("", panel)
        self.feedback_label.setWordWrap(True)
        self.open_management_button = QPushButton("Open Aquarium Management", panel)
        self.open_management_button.clicked.connect(self._open_aquarium_management)

        footer.addWidget(self.feedback_label, stretch=1)
        footer.addWidget(self.open_management_button)

        layout.addWidget(title)
        layout.addWidget(helper)
        layout.addLayout(controls)
        layout.addLayout(footer)
        return panel

    def _load_aquariums(self) -> None:
        self.aquariums = get_all_aquariums()
        self.aquarium_selector.clear()

        for aquarium in self.aquariums:
            label = f"{aquarium['id']}: {aquarium['name']} ({aquarium['volume']} L)"
            self.aquarium_selector.addItem(label, aquarium["id"])

        if self.aquarium_selector.count() == 0:
            self.aquarium_selector.addItem("No aquariums available", None)

        self._update_add_controls()

    def _update_catalog(self) -> None:
        fish_cards = search_fish_candidates(self.search_input.text().strip())
        self.catalog_list.clear()

        for card in fish_cards:
            aggression = card["parameters"]["aggression"]["value"]
            size = card["parameters"]["size"]["value"]
            item = QListWidgetItem(f"{card['name']} | {aggression} | {size}", self.catalog_list)
            item.setData(Qt.UserRole, card["id"])
            item.setData(Qt.UserRole + 1, card)

        if self.catalog_list.count() > 0:
            self.catalog_list.setCurrentRow(0)

    def _add_selected_candidate(self) -> None:
        item = self.catalog_list.currentItem()
        if item is None:
            self._set_catalog_feedback("Choose a fish from the catalog first.", error=True)
            return

        fish_id = int(item.data(Qt.UserRole))
        if fish_id in self.selected_fish_ids:
            self._set_catalog_feedback("This fish is already in the comparison list.", error=True)
            return

        if len(self.selected_fish_ids) >= MAX_FISH_TO_COMPARE:
            self._set_catalog_feedback(
                f"You can compare at most {MAX_FISH_TO_COMPARE} fish at once.",
                error=True,
            )
            return

        card = item.data(Qt.UserRole + 1)
        self.selected_fish_ids.append(fish_id)
        self.selected_fish_cards[fish_id] = card
        self._set_catalog_feedback(f"Added {card['name']} to the comparison.")
        self._refresh_selected_list()
        self._refresh_comparison()

    def _remove_selected_fish(self) -> None:
        item = self.selected_list.currentItem()
        if item is None:
            self._set_catalog_feedback("Choose a fish in the selected list first.", error=True)
            return

        fish_id = int(item.data(Qt.UserRole))
        self.selected_fish_ids = [current_id for current_id in self.selected_fish_ids if current_id != fish_id]
        self.selected_fish_cards.pop(fish_id, None)
        self._set_catalog_feedback("Removed fish from the comparison list.")
        self._refresh_selected_list()
        self._refresh_comparison()

    def _clear_selection(self) -> None:
        self.selected_fish_ids.clear()
        self.selected_fish_cards.clear()
        self._set_catalog_feedback("Comparison list cleared.")
        self._refresh_selected_list()
        self._refresh_comparison()

    def _refresh_selected_list(self) -> None:
        self.selected_list.clear()

        for fish_id in self.selected_fish_ids:
            card = self.selected_fish_cards.get(fish_id)
            if card is None:
                continue

            summary = (
                f"{card['name']} | "
                f"{card['parameters']['temperature']['value']} | "
                f"{card['parameters']['aggression']['value']}"
            )
            item = QListWidgetItem(summary, self.selected_list)
            item.setData(Qt.UserRole, fish_id)

        if self.selected_list.count() > 0:
            self.selected_list.setCurrentRow(0)

        self.selection_badge.setText(f"Selected: {len(self.selected_fish_ids)}/{MAX_FISH_TO_COMPARE}")
        self.remove_selected_button.setEnabled(self.selected_list.count() > 0)
        self.clear_selection_button.setEnabled(self.selected_list.count() > 0)

    def _refresh_comparison(self) -> None:
        if len(self.selected_fish_ids) < MIN_FISH_TO_COMPARE:
            self.overall_badge.setText("Status: choose fish")
            self.overall_badge.setStyleSheet(self._badge_style("#718096"))
            remaining = MIN_FISH_TO_COMPARE - len(self.selected_fish_ids)
            self.summary_label.setText(
                f"Add {remaining} more fish to start the compatibility comparison."
            )
            self.comparison_hint_label.setText(
                "Select at least two fish to see the table with temperature, pH, size, and aggression."
            )
            self._clear_cards()
            self.comparison_table.clear()
            self.comparison_table.setRowCount(0)
            self.comparison_table.setColumnCount(0)
            self.highlights_label.setText("No comparison highlights yet.")
            self._populate_add_fish_selector([])
            self._update_add_controls()
            return

        try:
            comparison = get_comparison_view_model(self.selected_fish_ids)["comparison"]
        except FishComparisonError as exc:
            self.overall_badge.setText("Status: error")
            self.overall_badge.setStyleSheet(self._badge_style("#C53030"))
            self.summary_label.setText(str(exc))
            self._populate_add_fish_selector([])
            self._update_add_controls()
            return

        self.selected_fish_cards = {
            card["id"]: card for card in comparison["selected_fish"]
        }
        self._refresh_selected_list()

        status_map = {
            "ok": ("Status: compatible", "#2F855A"),
            "warning": ("Status: caution", "#B7791F"),
            "critical": ("Status: conflict", "#C53030"),
        }
        status_text, status_color = status_map.get(comparison["overall_status"], ("Status: unknown", "#718096"))
        self.overall_badge.setText(status_text)
        self.overall_badge.setStyleSheet(self._badge_style(status_color))
        self.summary_label.setText(
            f"Compared {comparison['selected_count']} fish. {comparison['overall_label']}."
        )
        self.comparison_hint_label.setText(
            "Rows highlighted in yellow or red mark the most important compatibility differences."
        )

        self._render_cards(comparison["selected_fish"])
        self._populate_comparison_table(comparison["table_rows"])
        self._render_highlights(comparison["highlights"])
        self._populate_add_fish_selector(comparison["selected_fish"])
        self._update_add_controls()

    def _render_cards(self, fish_cards: list[dict]) -> None:
        self._clear_cards()
        columns = 3 if len(fish_cards) <= 3 else len(fish_cards)

        for index, card in enumerate(fish_cards):
            card_widget = QWidget(self.cards_panel)
            card_widget.setStyleSheet(
                "background-color: #FFFFFF; border: 1px solid #D6E4F0; border-radius: 12px;"
            )
            card_layout = QVBoxLayout(card_widget)
            card_layout.setContentsMargins(8, 8, 8, 8)
            card_layout.setSpacing(3)

            name_label = QLabel(card["name"], card_widget)
            name_label.setWordWrap(True)
            name_label.setStyleSheet("font-size: 13px; font-weight: 600; color: #1F4E79;")

            aggression_label = QLabel(
                f"Agg: {card['parameters']['aggression']['value']}",
                card_widget,
            )
            temperature_label = QLabel(
                f"T: {card['parameters']['temperature']['value']}",
                card_widget,
            )
            ph_label = QLabel(f"pH: {card['parameters']['ph']['value']}", card_widget)

            for label in (aggression_label, temperature_label, ph_label):
                label.setWordWrap(True)
                label.setStyleSheet("color: #4A5568; font-size: 11px;")
                card_layout.addWidget(label)

            card_layout.insertWidget(0, name_label)
            self.cards_layout.addWidget(card_widget, index // columns, index % columns)

    def _clear_cards(self) -> None:
        while self.cards_layout.count():
            item = self.cards_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()

    def _populate_comparison_table(self, table_rows: list[dict]) -> None:
        if not table_rows:
            self.comparison_table.clear()
            self.comparison_table.setRowCount(0)
            self.comparison_table.setColumnCount(0)
            return

        fish_headers = [entry["name"] for entry in table_rows[0]["fish_values"]]
        headers = ["Parameter", *fish_headers, "Insight"]

        self.comparison_table.clear()
        self.comparison_table.setColumnCount(len(headers))
        self.comparison_table.setRowCount(len(table_rows))
        self._set_compact_headers(headers)
        self.comparison_table.setColumnWidth(0, 130)

        for index in range(1, len(headers) - 1):
            self.comparison_table.setColumnWidth(index, 95)

        self.comparison_table.setColumnWidth(len(headers) - 1, 280)

        severity_colors = {
            "info": QColor("#EDF2F7"),
            "warning": QColor("#FEFCBF"),
            "critical": QColor("#FED7D7"),
        }

        for row_index, row in enumerate(table_rows):
            values = [row["label"], *[item["value"] for item in row["fish_values"]]]
            values.append(f"{row['summary']} | {row['insight']}")

            for column_index, value in enumerate(values):
                item = QTableWidgetItem(value)
                item.setFlags(item.flags() & ~Qt.ItemIsEditable)
                item.setTextAlignment(Qt.AlignLeft | Qt.AlignVCenter)
                item.setBackground(severity_colors[row["severity"]])
                self.comparison_table.setItem(row_index, column_index, item)

        self.comparison_table.resizeRowsToContents()

    def _set_compact_headers(self, headers: list[str]) -> None:
        for index, header in enumerate(headers):
            label = header
            if 0 < index < len(headers) - 1 and len(header) > 14:
                label = f"{header[:11]}..."

            item = QTableWidgetItem(label)
            item.setToolTip(header)
            self.comparison_table.setHorizontalHeaderItem(index, item)

    def _render_highlights(self, highlights: list[dict]) -> None:
        if not highlights:
            self.highlights_label.setText(
                "No significant differences detected in the current selection."
            )
            return

        parts = [f"{item['label']}: {item['message']}" for item in highlights]
        self.highlights_label.setText("Key differences: " + " | ".join(parts))

    def _populate_add_fish_selector(self, fish_cards: list[dict]) -> None:
        self.add_fish_selector.clear()

        for card in fish_cards:
            self.add_fish_selector.addItem(card["name"], card["id"])

        if self.add_fish_selector.count() == 0:
            self.add_fish_selector.addItem("Select fish to compare first", None)

    def _update_add_controls(self) -> None:
        aquarium_id = self.aquarium_selector.currentData()
        fish_id = self.add_fish_selector.currentData()
        comparison_ready = len(self.selected_fish_ids) >= MIN_FISH_TO_COMPARE
        self.add_to_aquarium_button.setEnabled(
            comparison_ready and aquarium_id is not None and fish_id is not None
        )

    def _handle_add_to_aquarium(self) -> None:
        aquarium_id = self.aquarium_selector.currentData()
        fish_id = self.add_fish_selector.currentData()

        if aquarium_id is None:
            self._set_feedback("Create or choose an aquarium first.", error=True)
            return

        if fish_id is None:
            self._set_feedback("Compare fish first, then choose one to add.", error=True)
            return

        quantity = self.quantity_input.value()
        result = add_fish_to_aquarium(int(aquarium_id), int(fish_id), quantity)
        if result.get("error"):
            self._set_feedback(self._translate_backend_message(result["error"]), error=True)
            return

        fish_name = self.add_fish_selector.currentText()
        self._set_feedback(
            f"Added {quantity} x {fish_name} to aquarium #{int(aquarium_id)}."
        )
        self._load_aquariums()

    def _open_aquarium_management(self) -> None:
        self.management_window = AquariumManagementPage()
        self.management_window.setWindowTitle("Proprif Fish - Manage Aquariums")
        self.management_window.show()

    def _open_all_fish_matrix_window(self) -> None:
        if self.all_fish_matrix_window is None:
            self.all_fish_matrix_window = AllFishMatrixWindow()

        self.all_fish_matrix_window.show()
        self.all_fish_matrix_window.raise_()
        self.all_fish_matrix_window.activateWindow()

    def _set_catalog_feedback(self, message: str, *, error: bool = False) -> None:
        color = "#C53030" if error else "#2F855A"
        self.catalog_feedback_label.setStyleSheet(f"color: {color};")
        self.catalog_feedback_label.setText(message)

    def _set_feedback(self, message: str, *, error: bool = False) -> None:
        color = "#C53030" if error else "#2F855A"
        self.feedback_label.setStyleSheet(f"color: {color};")
        self.feedback_label.setText(message)

        if error:
            QMessageBox.warning(self, "Action failed", message)

    @staticmethod
    def _badge_style(color: str) -> str:
        return (
            f"background-color: {color}; color: white; border-radius: 12px; "
            "padding: 6px 12px; font-weight: 600;"
        )

    @staticmethod
    def _panel_style() -> str:
        return (
            "background-color: #F7FAFC; border: 1px solid #E2E8F0; "
            "border-radius: 16px;"
        )

    @staticmethod
    def _translate_backend_message(message: str) -> str:
        translations = {
            "Kiekis turi bÅ«ti > 0": "Quantity must be greater than 0.",
            "Kiekis turi būti > 0": "Quantity must be greater than 0.",
            "Å½uvis nerasta": "Fish not found.",
            "Žuvis nerasta": "Fish not found.",
        }
        return translations.get(message, message)


if __name__ == "__main__":
    app = QApplication([])
    window = FishComparisonPage()
    window.setWindowTitle("Proprif Fish - Fish Compatibility")
    window.show()
    app.exec()
