"""Dedicated aquarium page for browsing multiple aquariums."""

from __future__ import annotations

import sqlite3
import sys
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QApplication,
    QDialog,
    QDialogButtonBox,
    QDoubleSpinBox,
    QFormLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
    QHBoxLayout,
    QVBoxLayout,
    QWidget,
)

try:
    from app.config import APP_DB
    from app.database.db_setup import create_tables
    from app.services.aquarium_load import calculate_tank_load
    from app.services.multiple_aquarium_logic import create_aquarium, get_all_aquariums
    from app.services.remove_fish_from_aquarium import (
        recalculate_aquarium_balance,
        remove_fish_from_aquarium,
    )
except ModuleNotFoundError:
    sys.path.append(str(Path(__file__).resolve().parents[2]))
    from app.config import APP_DB
    from app.database.db_setup import create_tables
    from app.services.aquarium_load import calculate_tank_load
    from app.services.multiple_aquarium_logic import create_aquarium, get_all_aquariums
    from app.services.remove_fish_from_aquarium import (
        recalculate_aquarium_balance,
        remove_fish_from_aquarium,
    )


class CreateAquariumDialog(QDialog):
    """Dialog for creating a new aquarium with the fields supported by the backend."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Add Aquarium")
        self.setModal(True)
        self.setMinimumWidth(360)

        layout = QVBoxLayout(self)
        form_layout = QFormLayout()

        self.name_input = QLineEdit(self)
        self.name_input.setPlaceholderText("Aquarium name")

        self.volume_input = QDoubleSpinBox(self)
        self.volume_input.setRange(1, 100000)
        self.volume_input.setDecimals(1)
        self.volume_input.setValue(54.0)
        self.volume_input.setSuffix(" L")

        form_layout.addRow("Name:", self.name_input)
        form_layout.addRow("Volume:", self.volume_input)
        layout.addLayout(form_layout)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel, self)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def get_values(self) -> tuple[str, float]:
        return self.name_input.text().strip(), float(self.volume_input.value())


class AquariumPage(QWidget):
    """Page for managing multiple aquariums and their fish combinations."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        create_tables()

        self.aquariums: list[dict] = []

        self.setMinimumSize(1180, 720)
        self.setStyleSheet("color: #111827; background-color: #F8FAFC;")
        self._build_ui()
        self._load_aquariums()

    def _build_ui(self) -> None:
        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(24, 24, 24, 24)
        root_layout.setSpacing(16)

        title = QLabel("Aquariums", self)
        title.setStyleSheet("font-size: 30px; font-weight: 700; color: #1E3A5F;")

        subtitle = QLabel(
            "Save multiple aquariums and plan different fish combinations for each one.",
            self,
        )
        subtitle.setWordWrap(True)
        subtitle.setStyleSheet("font-size: 14px; color: #475569;")

        content_layout = QHBoxLayout()
        content_layout.setSpacing(18)
        content_layout.addWidget(self._build_left_panel(), stretch=1)
        content_layout.addWidget(self._build_details_panel(), stretch=2)

        root_layout.addWidget(title)
        root_layout.addWidget(subtitle)
        root_layout.addLayout(content_layout, stretch=1)

    def _build_left_panel(self) -> QWidget:
        panel = QWidget(self)
        panel.setStyleSheet(self._panel_style())
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        title = QLabel("Saved Aquariums", panel)
        title.setStyleSheet("font-size: 20px; font-weight: 600; color: #0F766E;")

        helper = QLabel(
            "Choose an aquarium from the list to load its fish on the right.",
            panel,
        )
        helper.setWordWrap(True)
        helper.setStyleSheet("color: #4B5563;")

        self.add_aquarium_button = QPushButton("Add Aquarium", panel)
        self.add_aquarium_button.setFixedHeight(40)
        self.add_aquarium_button.clicked.connect(self._open_create_dialog)

        self.aquarium_list = QListWidget(panel)
        self.aquarium_list.currentItemChanged.connect(self._refresh_current_aquarium_view)
        self.aquarium_list.setStyleSheet(
            "QListWidget { background-color: white; border: 1px solid #D1D5DB; border-radius: 12px; padding: 6px; }"
            "QListWidget::item { padding: 10px; border-radius: 8px; }"
            "QListWidget::item:selected { background-color: #DBEAFE; color: #1E3A8A; }"
        )

        self.aquarium_count_label = QLabel("0 aquariums", panel)
        self.aquarium_count_label.setStyleSheet("color: #64748B;")

        layout.addWidget(title)
        layout.addWidget(helper)
        layout.addWidget(self.add_aquarium_button)
        layout.addWidget(self.aquarium_list, stretch=1)
        layout.addWidget(self.aquarium_count_label)
        return panel

    def _build_details_panel(self) -> QWidget:
        panel = QWidget(self)
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(18)

        layout.addWidget(self._build_overview_panel())
        layout.addWidget(self._build_fish_panel(), stretch=1)
        return panel

    def _build_overview_panel(self) -> QWidget:
        panel = QWidget(self)
        panel.setStyleSheet(self._panel_style())
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(10)

        self.aquarium_title_label = QLabel("Choose an aquarium", panel)
        self.aquarium_title_label.setStyleSheet("font-size: 24px; font-weight: 700; color: #7C2D12;")

        self.aquarium_summary_label = QLabel(
            "Select one aquarium from the left or create a new one.",
            panel,
        )
        self.aquarium_summary_label.setWordWrap(True)

        stats_layout = QHBoxLayout()
        stats_layout.setSpacing(12)

        self.compatibility_badge = QLabel("Status: -", panel)
        self.compatibility_badge.setAlignment(Qt.AlignCenter)
        self.compatibility_badge.setMinimumWidth(160)
        self.compatibility_badge.setStyleSheet(self._badge_style("#718096"))

        self.load_label = QLabel("Load: -", panel)
        self.temp_ph_label = QLabel("Temp/pH: -", panel)

        stats_layout.addWidget(self.compatibility_badge)
        stats_layout.addWidget(self.load_label)
        stats_layout.addWidget(self.temp_ph_label)
        stats_layout.addStretch(1)

        self.compatibility_details_label = QLabel(
            "Compatibility details will be shown for the selected aquarium.",
            panel,
        )
        self.compatibility_details_label.setWordWrap(True)
        self.compatibility_details_label.setStyleSheet("color: #334155;")

        self.feedback_label = QLabel("", panel)
        self.feedback_label.setWordWrap(True)
        self.feedback_label.setStyleSheet("color: #2F855A;")

        layout.addWidget(self.aquarium_title_label)
        layout.addWidget(self.aquarium_summary_label)
        layout.addLayout(stats_layout)
        layout.addWidget(self.compatibility_details_label)
        layout.addWidget(self.feedback_label)
        return panel

    def _build_fish_panel(self) -> QWidget:
        panel = QWidget(self)
        panel.setStyleSheet(self._panel_style())
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        title = QLabel("Fish In Aquarium", panel)
        title.setStyleSheet("font-size: 20px; font-weight: 600; color: #7C3AED;")

        self.aquarium_fish_list = QListWidget(panel)
        self.aquarium_fish_list.currentItemChanged.connect(self._update_remove_button_state)
        self.aquarium_fish_list.setStyleSheet("color: #111827; background-color: white;")

        controls = QHBoxLayout()
        controls.setSpacing(10)

        self.remove_button = QPushButton("Remove One Fish", panel)
        self.remove_button.setEnabled(False)
        self.remove_button.clicked.connect(self._handle_remove_fish)

        self.refresh_button = QPushButton("Refresh", panel)
        self.refresh_button.clicked.connect(self._refresh_current_aquarium_view)

        controls.addWidget(self.remove_button)
        controls.addWidget(self.refresh_button)

        layout.addWidget(title)
        layout.addWidget(self.aquarium_fish_list, stretch=1)
        layout.addLayout(controls)
        return panel

    def _load_aquariums(self, selected_aquarium_id: int | None = None) -> None:
        self.aquariums = get_all_aquariums()

        self.aquarium_list.blockSignals(True)
        self.aquarium_list.clear()

        selected_row = -1
        for index, aquarium in enumerate(self.aquariums):
            fish_count = len(aquarium["fish"])
            item = QListWidgetItem(
                f"{aquarium['name']}\n{aquarium['volume']} L • {fish_count} fish",
                self.aquarium_list,
            )
            item.setData(Qt.UserRole, aquarium["id"])
            if aquarium["id"] == selected_aquarium_id:
                selected_row = index

        self.aquarium_list.blockSignals(False)
        self.aquarium_count_label.setText(f"{len(self.aquariums)} aquariums")

        if not self.aquariums:
            self._clear_aquarium_details()
            return

        if selected_row == -1:
            selected_row = 0

        self.aquarium_list.setCurrentRow(selected_row)
        self._refresh_current_aquarium_view()

    def _selected_aquarium(self) -> dict | None:
        item = self.aquarium_list.currentItem()
        if item is None:
            return None

        aquarium_id = int(item.data(Qt.UserRole))
        return next((row for row in self.aquariums if int(row["id"]) == aquarium_id), None)

    def _selected_aquarium_id(self) -> int | None:
        aquarium = self._selected_aquarium()
        return None if aquarium is None else int(aquarium["id"])

    def _open_create_dialog(self) -> None:
        dialog = CreateAquariumDialog(self)
        if dialog.exec() != QDialog.Accepted:
            return

        name, volume = dialog.get_values()
        result = create_aquarium(name, volume)

        if not result.get("success"):
            self._set_feedback(result.get("message", "Failed to create aquarium."), error=True)
            return

        created = result["aquarium"]
        self._set_feedback(f"Aquarium '{created['name']}' created successfully.")
        self._load_aquariums(selected_aquarium_id=int(created["id"]))

    def _handle_remove_fish(self) -> None:
        aquarium_id = self._selected_aquarium_id()
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

        self._set_feedback(f"Removed 1 x {fish_name} from the selected aquarium.")
        self._load_aquariums(selected_aquarium_id=aquarium_id)

    def _refresh_current_aquarium_view(self) -> None:
        aquarium_id = self._selected_aquarium_id()
        self.aquariums = get_all_aquariums()
        aquarium = next((row for row in self.aquariums if int(row["id"]) == aquarium_id), None)

        self.aquarium_fish_list.clear()

        if aquarium is None:
            self._clear_aquarium_details()
            return

        self.aquarium_title_label.setText(str(aquarium["name"]))

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
            f"{aquarium['volume']} L aquarium with {total_fish} fish across {species_count} species."
        )

        self._update_compatibility_labels(aquarium_id)
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
            "Use this aquarium to plan different fish combinations."
        )

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

    def _clear_aquarium_details(self) -> None:
        self.aquarium_title_label.setText("Choose an aquarium")
        self.aquarium_summary_label.setText(
            "Create a new aquarium or select one from the list on the left."
        )
        self.compatibility_badge.setText("Status: -")
        self.compatibility_badge.setStyleSheet(self._badge_style("#718096"))
        self.load_label.setText("Load: -")
        self.temp_ph_label.setText("Temp/pH: -")
        self.compatibility_details_label.setText(
            "Compatibility details will be shown for the selected aquarium."
        )
        self.aquarium_fish_list.clear()
        self._set_feedback("")
        self._update_remove_button_state()

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
    window = AquariumPage()
    window.setWindowTitle("Proprif Fish - Aquariums")
    window.show()
    app.exec()
