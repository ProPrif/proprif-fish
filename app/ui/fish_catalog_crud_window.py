"""Fish catalog CRUD window UI."""

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
    QHBoxLayout,
    QWidget,
    QLineEdit,
    QDoubleSpinBox,
    QMessageBox,
    QGroupBox,
    QComboBox,
)

from app.services import fish_logic


class FishCatalogCrudWindow(QMainWindow):
    """Window that displays fish catalog with integrated CRUD operations."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Fish Catalog")
        self.setMinimumSize(1000, 650)
        self.current_editing_id = None

        container = QWidget(self)
        layout = QVBoxLayout(container)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(12)

        header = QLabel("Fish Catalog", container)
        header.setAlignment(Qt.AlignLeft)
        header.setStyleSheet("font-size: 20px; font-weight: 700; color: #E8F0FF;")
        layout.addWidget(header)

        self._table = QTableWidget(container)
        self._table.setColumnCount(8)
        self._table.setHorizontalHeaderLabels(["ID", "Name", "Aggression", "Size", "Temp Min", "Temp Max", "pH Min", "pH Max"])
        self._table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self._table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self._table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self._table.setSelectionMode(QAbstractItemView.SingleSelection)
        self._table.itemSelectionChanged.connect(self._update_details)
        layout.addWidget(self._table)

        self._details = QLabel("Select a fish to view details.", container)
        self._details.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        self._details.setStyleSheet("font-size: 13px; font-weight: 500; color: #C9D7F2;")
        self._details.setWordWrap(True)
        layout.addWidget(self._details)

        form_group = QGroupBox("Add/Edit Fish", container)
        form_layout = QVBoxLayout(form_group)

        form_fields_layout = QHBoxLayout()
        
        self._form_name = QLineEdit()
        self._form_name.setPlaceholderText("Fish Name")
        self._form_name.setMaximumWidth(150)
        form_fields_layout.addWidget(QLabel("Name:"))
        form_fields_layout.addWidget(self._form_name)

        self._form_aggression = QComboBox()
        self._form_aggression.addItems(["PEACEFUL", "SEMI-AGGRESSIVE", "AGGRESSIVE"])
        self._form_aggression.setMaximumWidth(150)
        form_fields_layout.addWidget(QLabel("Aggression:"))
        form_fields_layout.addWidget(self._form_aggression)

        self._form_size = QDoubleSpinBox()
        self._form_size.setRange(0, 50)
        self._form_size.setMaximumWidth(100)
        form_fields_layout.addWidget(QLabel("Size:"))
        form_fields_layout.addWidget(self._form_size)

        self._form_temp_min = QDoubleSpinBox()
        self._form_temp_min.setRange(-10, 50)
        self._form_temp_min.setMaximumWidth(100)
        form_fields_layout.addWidget(QLabel("Temp Min:"))
        form_fields_layout.addWidget(self._form_temp_min)

        self._form_temp_max = QDoubleSpinBox()
        self._form_temp_max.setRange(-10, 50)
        self._form_temp_max.setMaximumWidth(100)
        form_fields_layout.addWidget(QLabel("Temp Max:"))
        form_fields_layout.addWidget(self._form_temp_max)

        self._form_ph_min = QDoubleSpinBox()
        self._form_ph_min.setRange(0, 14)
        self._form_ph_min.setDecimals(1)
        self._form_ph_min.setMaximumWidth(100)
        form_fields_layout.addWidget(QLabel("pH Min:"))
        form_fields_layout.addWidget(self._form_ph_min)

        self._form_ph_max = QDoubleSpinBox()
        self._form_ph_max.setRange(0, 14)
        self._form_ph_max.setDecimals(1)
        self._form_ph_max.setMaximumWidth(100)
        form_fields_layout.addWidget(QLabel("pH Max:"))
        form_fields_layout.addWidget(self._form_ph_max)

        form_layout.addLayout(form_fields_layout)

        form_buttons_layout = QHBoxLayout()
        
        save_button = QPushButton("Save")
        save_button.setFixedHeight(28)
        save_button.setMaximumWidth(100)
        save_button.clicked.connect(self._save_fish)
        form_buttons_layout.addWidget(save_button)

        cancel_button = QPushButton("Cancel")
        cancel_button.setFixedHeight(28)
        cancel_button.setMaximumWidth(100)
        cancel_button.clicked.connect(self._cancel_form)
        form_buttons_layout.addWidget(cancel_button)

        form_buttons_layout.addStretch(1)
        form_layout.addLayout(form_buttons_layout)

        self._form_group = form_group
        self._form_group.setVisible(False)
        layout.addWidget(self._form_group)

        buttons_layout = QHBoxLayout()
        buttons_layout.setSpacing(8)

        add_button = QPushButton("Add Fish")
        add_button.setFixedHeight(32)
        add_button.clicked.connect(self._open_add_fish_dialog)

        edit_button = QPushButton("Edit Fish")
        edit_button.setFixedHeight(32)
        edit_button.clicked.connect(self._open_edit_fish_dialog)

        delete_button = QPushButton("Delete Fish")
        delete_button.setFixedHeight(32)
        delete_button.clicked.connect(self._delete_selected_fish)

        close_button = QPushButton("Close")
        close_button.setFixedHeight(32)
        close_button.clicked.connect(self.close)

        buttons_layout.addWidget(add_button)
        buttons_layout.addWidget(edit_button)
        buttons_layout.addWidget(delete_button)
        buttons_layout.addStretch(1)
        buttons_layout.addWidget(close_button)

        layout.addLayout(buttons_layout)

        self.setCentralWidget(container)
        self._load_fish_list()

    def _load_fish_list(self) -> None:
        rows = fish_logic.get_all_fish()
        self._table.setRowCount(len(rows))

        for row_index, fish in enumerate(rows):
            self._table.setItem(row_index, 0, QTableWidgetItem(str(fish['id'])))
            self._table.setItem(row_index, 1, QTableWidgetItem(fish['fish_name']))
            self._table.setItem(row_index, 2, QTableWidgetItem(str(fish['aggression'])))
            self._table.setItem(row_index, 3, QTableWidgetItem(str(fish['size'])))
            self._table.setItem(row_index, 4, QTableWidgetItem(str(fish['temp_min'])))
            self._table.setItem(row_index, 5, QTableWidgetItem(str(fish['temp_max'])))
            self._table.setItem(row_index, 6, QTableWidgetItem(str(fish['ph_min'])))
            self._table.setItem(row_index, 7, QTableWidgetItem(str(fish['ph_max'])))

        if rows:
            self._table.selectRow(0)
            self._update_details()

    def _update_details(self) -> None:
        items = self._table.selectedItems()
        if not items:
            self._details.setText("Select a fish to view details.")
            return

        fish_id = int(items[0].text())
        fish = fish_logic.get_fish_by_id(fish_id)
        if not fish:
            self._details.setText("No details found for this fish.")
            return

        text = (
            f"Name: {fish['fish_name']}\n"
            f"Aggression: {fish['aggression']}\n"
            f"Size: {fish['size']}\n"
            f"Temperature Range: {fish['temp_min']}°C - {fish['temp_max']}°C\n"
            f"pH Range: {fish['ph_min']} - {fish['ph_max']}"
        )
        self._details.setText(text)

    def _clear_form(self) -> None:
        """Clear all form fields."""
        self._form_name.clear()
        self._form_aggression.setCurrentIndex(0)
        self._form_size.setValue(0)
        self._form_temp_min.setValue(0)
        self._form_temp_max.setValue(0)
        self._form_ph_min.setValue(0)
        self._form_ph_max.setValue(0)
        self.current_editing_id = None

    def _open_add_fish_dialog(self) -> None:
        """Show form to add a new fish."""
        self._clear_form()
        self._form_group.setTitle("Add New Fish")
        self._form_group.setVisible(True)
        self._form_name.setFocus()

    def _open_edit_fish_dialog(self) -> None:
        """Show form to edit selected fish."""
        items = self._table.selectedItems()
        if not items:
            QMessageBox.warning(self, "Warning", "Please select a fish to edit.")
            return

        fish_id = int(items[0].text())
        fish = fish_logic.get_fish_by_id(fish_id)
        if not fish:
            QMessageBox.warning(self, "Warning", "Could not load fish details.")
            return

        self.current_editing_id = fish_id
        self._form_name.setText(fish['fish_name'])
        self._form_aggression.setCurrentText(fish['aggression'])
        self._form_size.setValue(float(fish['size']))
        self._form_temp_min.setValue(float(fish['temp_min']))
        self._form_temp_max.setValue(float(fish['temp_max']))
        self._form_ph_min.setValue(float(fish['ph_min']))
        self._form_ph_max.setValue(float(fish['ph_max']))

        self._form_group.setTitle("Edit Fish")
        self._form_group.setVisible(True)
        self._form_name.setFocus()

    def _save_fish(self) -> None:
        """Save fish (add or edit)."""
        fish_name = self._form_name.text().strip()
        if not fish_name:
            QMessageBox.warning(self, "Validation Error", "Please enter a fish name.")
            return

        aggression = self._form_aggression.currentText()
        size = self._form_size.value()
        temp_min = self._form_temp_min.value()
        temp_max = self._form_temp_max.value()
        ph_min = self._form_ph_min.value()
        ph_max = self._form_ph_max.value()

        if temp_min >= temp_max:
            QMessageBox.warning(self, "Validation Error", "Temp Min must be less than Temp Max.")
            return

        if ph_min >= ph_max:
            QMessageBox.warning(self, "Validation Error", "pH Min must be less than pH Max.")
            return

        if self.current_editing_id is None:
            result = fish_logic.add_fish(fish_name, aggression, size, temp_min, temp_max, ph_min, ph_max)
            if result:
                QMessageBox.information(self, "Success", "Fish added successfully!")
                self._cancel_form()
                self._load_fish_list()
            else:
                QMessageBox.critical(self, "Error", "Failed to add fish.")
        else:
            result = fish_logic.update_fish(self.current_editing_id, fish_name, aggression, size, temp_min, temp_max, ph_min, ph_max)
            if result:
                QMessageBox.information(self, "Success", "Fish updated successfully!")
                self._cancel_form()
                self._load_fish_list()
            else:
                QMessageBox.critical(self, "Error", "Failed to update fish.")

    def _cancel_form(self) -> None:
        """Hide the form."""
        self._form_group.setVisible(False)
        self._clear_form()

    def _delete_selected_fish(self) -> None:
        """Delete the selected fish."""
        items = self._table.selectedItems()
        if not items:
            QMessageBox.warning(self, "Warning", "Please select a fish to delete.")
            return

        fish_id = int(items[0].text())
        fish = fish_logic.get_fish_by_id(fish_id)
        if not fish:
            QMessageBox.warning(self, "Warning", "Could not find fish to delete.")
            return

        reply = QMessageBox.question(
            self,
            "Confirm Delete",
            f"Are you sure you want to delete '{fish['fish_name']}'?",
            QMessageBox.Yes | QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            if fish_logic.delete_fish(fish_id):
                QMessageBox.information(self, "Success", "Fish deleted successfully!")
                self._load_fish_list()
            else:
                QMessageBox.critical(self, "Error", "Failed to delete fish.")

