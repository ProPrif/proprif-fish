"""Aquarium management UI connected to the existing backend services."""

from __future__ import annotations

import sqlite3
import sys
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QApplication,
    QComboBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

try:
    from app.config import APP_DB
    from app.database.db_setup import create_tables
    from app.services.aquarium_load import calculate_tank_load
    from app.services.multiple_aquarium_logic import get_all_aquariums
    from app.services.aquarium_indicator_logic import CompatibilityChecker
    from app.services.remove_fish_from_aquarium import (
        recalculate_aquarium_balance,
        remove_fish_from_aquarium,
    )
    from app.services.search_and_add_fish import add_fish_to_aquarium, search_fish
except ModuleNotFoundError:
    sys.path.append(str(Path(__file__).resolve().parents[2]))
    from app.config import APP_DB
    from app.database.db_setup import create_tables
    from app.services.aquarium_load import calculate_tank_load
    from app.services.multiple_aquarium_logic import get_all_aquariums
    from app.services.aquarium_indicator_logic import CompatibilityChecker
    from app.services.remove_fish_from_aquarium import (
        recalculate_aquarium_balance,
        remove_fish_from_aquarium,
    )
    from app.services.search_and_add_fish import add_fish_to_aquarium, search_fish


class AquariumManagementPage(QWidget):
    """UI for adding and removing fish from aquariums."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        create_tables()

        self.aquariums: list[dict] = []

        self.setMinimumSize(960, 620)
        self.setStyleSheet("color: #111827; background-color: #F8FAFC;")
        self._build_ui()
        self._load_aquariums()

    def _build_ui(self) -> None:
        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(24, 24, 24, 24)
        root_layout.setSpacing(16)

        header = QLabel("Aquarium Fish Management", self)
        header.setStyleSheet("font-size: 28px; font-weight: 700; color: #1F4E79;")

        subtitle = QLabel(
            "Find fish in the catalog, choose quantity, add them to an aquarium, "
            "and update compatibility instantly after each change.",
            self,
        )
        subtitle.setWordWrap(True)
        subtitle.setStyleSheet("font-size: 14px; color: #4A5568;")

        root_layout.addWidget(header)
        root_layout.addWidget(subtitle)
        root_layout.addWidget(self._build_top_controls())

        content_layout = QHBoxLayout()
        content_layout.setSpacing(18)
        content_layout.addWidget(self._build_search_panel(), stretch=1)
        content_layout.addWidget(self._build_aquarium_panel(), stretch=1)

        root_layout.addLayout(content_layout, stretch=1)

    def _build_top_controls(self) -> QWidget:
        panel = QWidget(self)
        layout = QHBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)

        layout.addWidget(QLabel("Aquarium:", panel))

        self.aquarium_selector = QComboBox(panel)
        self.aquarium_selector.currentIndexChanged.connect(self._refresh_current_aquarium_view)
        layout.addWidget(self.aquarium_selector, stretch=1)

        self.compatibility_badge = QLabel("Status: -", panel)
        self.compatibility_badge.setAlignment(Qt.AlignCenter)
        self.compatibility_badge.setMinimumWidth(160)
        self.compatibility_badge.setStyleSheet(self._badge_style("#718096"))

        self.load_label = QLabel("Load: -", panel)
        self.temp_ph_label = QLabel("Temp/pH: -", panel)

        layout.addWidget(self.compatibility_badge)
        layout.addWidget(self.load_label)
        layout.addWidget(self.temp_ph_label)
        return panel

    def _build_search_panel(self) -> QWidget:
        panel = QWidget(self)
        panel.setStyleSheet(self._panel_style())
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        title = QLabel("Fish Catalog", panel)
        title.setStyleSheet("font-size: 20px; font-weight: 600; color: #234E52;")

        self.search_input = QLineEdit(panel)
        self.search_input.setPlaceholderText("Search fish by name...")
        self.search_input.textChanged.connect(self._update_search_results)
        self.search_input.setStyleSheet("color: #111827; background-color: white;")

        self.search_results = QListWidget(panel)
        self.search_results.currentItemChanged.connect(self._update_selected_fish_label)
        self.search_results.setStyleSheet("color: #111827; background-color: white;")

        quantity_row = QHBoxLayout()
        quantity_row.addWidget(QLabel("Quantity:", panel))

        self.quantity_input = QSpinBox(panel)
        self.quantity_input.setRange(1, 999)
        self.quantity_input.setValue(1)
        self.quantity_input.setStyleSheet("color: #111827; background-color: white;")
        self.quantity_input.valueChanged.connect(self._refresh_candidate_indicator)
        quantity_row.addWidget(self.quantity_input)
        quantity_row.addStretch(1)

        self.selected_fish_label = QLabel("Selected fish: none", panel)
        self.selected_fish_label.setStyleSheet("color: #4A5568;")

        indicator_card = QWidget(panel)
        indicator_card.setStyleSheet(
            "background-color: white; border: 1px solid #CBD5E0; border-radius: 12px;"
        )
        indicator_layout = QVBoxLayout(indicator_card)
        indicator_layout.setContentsMargins(12, 12, 12, 12)
        indicator_layout.setSpacing(8)

        indicator_title = QLabel("Selected Fish Compatibility", indicator_card)
        indicator_title.setStyleSheet("font-size: 15px; font-weight: 600; color: #1F2937;")

        indicator_header = QHBoxLayout()
        indicator_header.setSpacing(8)

        self.candidate_indicator_button = QToolButton(indicator_card)
        self.candidate_indicator_button.setText("Status: -")
        self.candidate_indicator_button.setToolButtonStyle(Qt.ToolButtonTextOnly)
        self.candidate_indicator_button.setCursor(Qt.PointingHandCursor)
        self.candidate_indicator_button.clicked.connect(self._toggle_candidate_details)
        self.candidate_indicator_button.setStyleSheet(self._badge_style("#718096"))

        self.candidate_indicator_hint = QLabel(
            "Click the indicator to show or hide mismatch codes.",
            indicator_card,
        )
        self.candidate_indicator_hint.setWordWrap(True)
        self.candidate_indicator_hint.setStyleSheet("color: #4B5563;")

        indicator_header.addWidget(self.candidate_indicator_button)
        indicator_header.addWidget(self.candidate_indicator_hint, stretch=1)

        self.candidate_summary_label = QLabel(
            "Choose a fish and quantity to preview aquarium compatibility.",
            indicator_card,
        )
        self.candidate_summary_label.setWordWrap(True)
        self.candidate_summary_label.setStyleSheet("color: #1F2937;")

        self.candidate_details_label = QLabel("", indicator_card)
        self.candidate_details_label.setWordWrap(True)
        self.candidate_details_label.setStyleSheet(
            "color: #7F1D1D; background-color: #FEF2F2; border-radius: 8px; padding: 8px;"
        )
        self.candidate_details_label.hide()

        indicator_layout.addWidget(indicator_title)
        indicator_layout.addLayout(indicator_header)
        indicator_layout.addWidget(self.candidate_summary_label)
        indicator_layout.addWidget(self.candidate_details_label)

        self.add_button = QPushButton("Add To Aquarium", panel)
        self.add_button.clicked.connect(self._handle_add_fish)

        self.feedback_label = QLabel("", panel)
        self.feedback_label.setWordWrap(True)

        layout.addWidget(title)
        layout.addWidget(self.search_input)
        layout.addWidget(self.search_results, stretch=1)
        layout.addLayout(quantity_row)
        layout.addWidget(self.selected_fish_label)
        layout.addWidget(indicator_card)
        layout.addWidget(self.add_button)
        layout.addWidget(self.feedback_label)
        return panel

    def _build_aquarium_panel(self) -> QWidget:
        panel = QWidget(self)
        panel.setStyleSheet(self._panel_style())
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        title = QLabel("Current Aquarium Fish", panel)
        title.setStyleSheet("font-size: 20px; font-weight: 600; color: #744210;")

        self.aquarium_summary_label = QLabel("Choose an aquarium to see its fish.", panel)
        self.aquarium_summary_label.setWordWrap(True)

        self.aquarium_fish_list = QListWidget(panel)
        self.aquarium_fish_list.currentItemChanged.connect(self._update_remove_button_state)
        self.aquarium_fish_list.setStyleSheet("color: #111827; background-color: white;")

        controls_row = QHBoxLayout()

        self.remove_button = QPushButton("Remove One Fish", panel)
        self.remove_button.setEnabled(False)
        self.remove_button.clicked.connect(self._handle_remove_fish)

        self.refresh_button = QPushButton("Refresh", panel)
        self.refresh_button.clicked.connect(self._refresh_current_aquarium_view)

        controls_row.addWidget(self.remove_button)
        controls_row.addWidget(self.refresh_button)

        self.compatibility_details_label = QLabel(
            "Compatibility details will appear here after aquarium data is loaded.",
            panel,
        )
        self.compatibility_details_label.setWordWrap(True)
        self.compatibility_details_label.setStyleSheet("color: #2D3748;")

        layout.addWidget(title)
        layout.addWidget(self.aquarium_summary_label)
        layout.addWidget(self.aquarium_fish_list, stretch=1)
        layout.addLayout(controls_row)
        layout.addWidget(self.compatibility_details_label)
        return panel

    def _load_aquariums(self) -> None:
        self.aquariums = get_all_aquariums()

        self.aquarium_selector.blockSignals(True)
        self.aquarium_selector.clear()
        for aquarium in self.aquariums:
            label = f"{aquarium['id']}: {aquarium['name']} ({aquarium['volume']} L)"
            self.aquarium_selector.addItem(label, aquarium["id"])
        self.aquarium_selector.blockSignals(False)

        self._update_search_results()
        self._refresh_current_aquarium_view()

    def _update_search_results(self) -> None:
        fish_rows = search_fish(self.search_input.text().strip())

        self.search_results.clear()
        for fish_id, fish_name, aggression, size in fish_rows:
            item = QListWidgetItem(
                f"{fish_name} | {aggression} | {size:.2f} cm",
                self.search_results,
            )
            item.setData(Qt.UserRole, fish_id)
            item.setData(Qt.UserRole + 1, fish_name)

        if self.search_results.count() > 0:
            self.search_results.setCurrentRow(0)
        else:
            self.selected_fish_label.setText("Selected fish: none")
            self._clear_candidate_indicator()

    def _update_selected_fish_label(self) -> None:
        item = self.search_results.currentItem()
        if item is None:
            self.selected_fish_label.setText("Selected fish: none")
            self._clear_candidate_indicator()
            return

        self.selected_fish_label.setText(f"Selected fish: {item.data(Qt.UserRole + 1)}")
        self._refresh_candidate_indicator()

    def _current_aquarium_id(self) -> int | None:
        current_data = self.aquarium_selector.currentData()
        return None if current_data is None else int(current_data)

    def _handle_add_fish(self) -> None:
        aquarium_id = self._current_aquarium_id()
        if aquarium_id is None:
            self._set_feedback("No aquarium selected.", error=True)
            return

        item = self.search_results.currentItem()
        if item is None:
            self._set_feedback("Choose a fish from the search results first.", error=True)
            return

        quantity = self.quantity_input.value()
        fish_id = int(item.data(Qt.UserRole))
        fish_name = str(item.data(Qt.UserRole + 1))

        result = add_fish_to_aquarium(aquarium_id, fish_id, quantity)
        if result.get("error"):
            self._set_feedback(result["error"], error=True)
            return

        self._set_feedback(f"Added {quantity} x {fish_name} to aquarium #{aquarium_id}.")
        self._refresh_current_aquarium_view()

    def _handle_remove_fish(self) -> None:
        aquarium_id = self._current_aquarium_id()
        item = self.aquarium_fish_list.currentItem()

        if aquarium_id is None or item is None:
            self._set_feedback("Choose a fish in the aquarium list first.", error=True)
            return

        fish_id = int(item.data(Qt.UserRole))
        fish_name = str(item.data(Qt.UserRole + 1))
        record_id = self._first_matching_aquarium_record(aquarium_id, fish_id)

        if record_id is None:
            self._set_feedback("Selected fish is no longer in this aquarium.", error=True)
            return

        result = remove_fish_from_aquarium(aquarium_id, fish_id, record_id)
        if result.get("error"):
            self._set_feedback(result["error"], error=True)
            return

        self._set_feedback(f"Removed 1 x {fish_name} from aquarium #{aquarium_id}.")
        self._refresh_current_aquarium_view()

    def _refresh_current_aquarium_view(self) -> None:
        aquarium_id = self._current_aquarium_id()
        self.aquariums = get_all_aquariums()
        aquarium = next((item for item in self.aquariums if item["id"] == aquarium_id), None)

        self.aquarium_fish_list.clear()

        if aquarium is None:
            self.aquarium_summary_label.setText("No aquarium selected.")
            self.compatibility_badge.setText("Status: -")
            self.compatibility_badge.setStyleSheet(self._badge_style("#718096"))
            self.load_label.setText("Load: -")
            self.temp_ph_label.setText("Temp/pH: -")
            self.compatibility_details_label.setText(
                "Compatibility details will appear here after aquarium data is loaded."
            )
            self._clear_candidate_indicator()
            self._update_remove_button_state()
            return

        grouped_fish: dict[int, dict[str, object]] = {}
        for fish in aquarium["fish"]:
            fish_id = int(fish["id"])
            if fish_id not in grouped_fish:
                grouped_fish[fish_id] = {
                    "name": fish["name"],
                    "count": 0,
                    "aggression": fish["aggression"],
                }
            grouped_fish[fish_id]["count"] = int(grouped_fish[fish_id]["count"]) + 1

        for fish_id, fish_data in sorted(grouped_fish.items(), key=lambda row: str(row[1]["name"]).lower()):
            item = QListWidgetItem(
                f"{fish_data['name']} | qty: {fish_data['count']} | {fish_data['aggression']}",
                self.aquarium_fish_list,
            )
            item.setData(Qt.UserRole, fish_id)
            item.setData(Qt.UserRole + 1, fish_data["name"])

        total_fish = sum(int(data["count"]) for data in grouped_fish.values())
        species_count = len(grouped_fish)
        self.aquarium_summary_label.setText(
            f"{aquarium['name']} ({aquarium['volume']} L) currently has "
            f"{total_fish} fish across {species_count} species."
        )

        self._update_compatibility_labels(aquarium["id"])
        self._refresh_candidate_indicator()
        self._update_remove_button_state()

    def _update_compatibility_labels(self, aquarium_id: int) -> None:
        overall_status = recalculate_aquarium_balance(aquarium_id)
        load_result = calculate_tank_load(aquarium_id)
        temp_ph_summary = self._calculate_temp_ph_summary(aquarium_id)

        status_map = {
            "GREEN": ("Status: GREEN", "#2F855A"),
            "YELLOW": ("Status: YELLOW", "#B7791F"),
            "RED": ("Status: RED", "#C53030"),
            "EMPTY": ("Status: EMPTY", "#718096"),
            "UNKNOWN": ("Status: UNKNOWN", "#718096"),
        }
        badge_text, badge_color = status_map.get(overall_status, ("Status: -", "#718096"))
        self.compatibility_badge.setText(badge_text)
        self.compatibility_badge.setStyleSheet(self._badge_style(badge_color))

        if isinstance(load_result, dict) and "error" not in load_result:
            self.load_label.setText(
                f"Load: {load_result['needed_litres']:.2f}/{load_result['tank_volume']:.2f} L"
            )
        else:
            self.load_label.setText("Load: unknown")

        self.temp_ph_label.setText(temp_ph_summary)
        self.compatibility_details_label.setText(
            f"Overall compatibility is {overall_status}. {temp_ph_summary}. "
            "The view refreshes immediately after add or remove actions."
        )

    def _refresh_candidate_indicator(self) -> None:
        aquarium_id = self._current_aquarium_id()
        item = self.search_results.currentItem()

        if aquarium_id is None or item is None:
            self._clear_candidate_indicator()
            return

        fish_id = int(item.data(Qt.UserRole))
        fish_name = str(item.data(Qt.UserRole + 1))
        quantity = self.quantity_input.value()

        result = CompatibilityChecker.evaluate_candidate_for_aquarium(
            aquarium_id=aquarium_id,
            fish_id=fish_id,
            quantity_to_add=quantity,
        )

        status_map = {
            "GREEN": ("Status: GREEN", "#2F855A"),
            "YELLOW": ("Status: YELLOW", "#B7791F"),
            "RED": ("Status: RED", "#C53030"),
        }
        status_text, status_color = status_map.get(result.get("status"), ("Status: -", "#718096"))
        self.candidate_indicator_button.setText(status_text)
        self.candidate_indicator_button.setStyleSheet(self._badge_style(status_color))

        aquarium_name = result.get("aquarium_name") or f"Aquarium #{aquarium_id}"
        self.candidate_summary_label.setText(
            f"{fish_name} x {quantity} preview for {aquarium_name}: {result.get('label', 'Unknown')}"
        )

        details_lines = []
        for code, message in zip(result.get("codes", []), result.get("messages", [])):
            details_lines.append(f"{code}: {message}")

        self.candidate_details_label.setText("\n".join(details_lines))

    def _toggle_candidate_details(self) -> None:
        if not self.candidate_details_label.text().strip():
            return
        self.candidate_details_label.setVisible(not self.candidate_details_label.isVisible())

    def _clear_candidate_indicator(self) -> None:
        self.candidate_indicator_button.setText("Status: -")
        self.candidate_indicator_button.setStyleSheet(self._badge_style("#718096"))
        self.candidate_summary_label.setText(
            "Choose a fish and quantity to preview aquarium compatibility."
        )
        self.candidate_details_label.clear()
        self.candidate_details_label.hide()

    def _calculate_temp_ph_summary(self, aquarium_id: int) -> str:
        conn = sqlite3.connect(APP_DB)
        try:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT fl.temp_min, fl.temp_max, fl.ph_min, fl.ph_max
                FROM fish_in_aquarium fia
                JOIN fish_list fl ON fia.fish_id = fl.id
                WHERE fia.aquarium_id = ?
                """,
                (aquarium_id,),
            )
            rows = cursor.fetchall()
        finally:
            conn.close()

        if not rows:
            return "Temp/pH: no fish"

        temp_min = max(row[0] for row in rows)
        temp_max = min(row[1] for row in rows)
        ph_min = max(row[2] for row in rows)
        ph_max = min(row[3] for row in rows)

        if temp_min > temp_max or ph_min > ph_max:
            return "Temp/pH: incompatible"

        return f"Temp/pH: {temp_min:.1f}-{temp_max:.1f} C | pH {ph_min:.1f}-{ph_max:.1f}"

    def _first_matching_aquarium_record(self, aquarium_id: int, fish_id: int) -> int | None:
        conn = sqlite3.connect(APP_DB)
        try:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT id
                FROM fish_in_aquarium
                WHERE aquarium_id = ? AND fish_id = ?
                ORDER BY id ASC
                LIMIT 1
                """,
                (aquarium_id, fish_id),
            )
            row = cursor.fetchone()
        finally:
            conn.close()

        return None if row is None else int(row[0])

    def _update_remove_button_state(self) -> None:
        self.remove_button.setEnabled(self.aquarium_fish_list.currentItem() is not None)

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


if __name__ == "__main__":
    app = QApplication([])
    window = AquariumManagementPage()
    window.setWindowTitle("Proprif Fish - Aquarium Management")
    window.show()
    app.exec()
