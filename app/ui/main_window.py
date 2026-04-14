"""Main window UI for the desktop app."""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLabel, QMainWindow, QPushButton, QVBoxLayout, QWidget

from app.ui.aquarium_management_page import AquariumManagementPage
from app.ui.aquarium_page import AquariumPage
from app.ui.fish_select_window import FishSelectWindow
from app.ui.history_window import HistoryWindow


class MainWindow(QMainWindow):
	"""Minimal welcome window for the application."""

	def __init__(self) -> None:
		super().__init__()
		self.setWindowTitle("Proprif Fish")
		self.setMinimumSize(640, 360)

		container = QWidget(self)
		layout = QVBoxLayout(container)
		layout.setContentsMargins(24, 24, 24, 24)
		layout.setSpacing(12)
		self.management_window = None
		self.aquarium_window = None
		self.fish_select_window = None
		self.history_window = None

		layout.addWidget(self._build_welcome_page())
		self.setCentralWidget(container)

	def _build_welcome_page(self) -> QWidget:
		page = QWidget(self)
		layout = QVBoxLayout(page)
		layout.setContentsMargins(24, 24, 24, 24)
		layout.setSpacing(12)

		title = QLabel("Welcome to Proprif Fish", page)
		title.setAlignment(Qt.AlignCenter)
		title.setStyleSheet("font-size: 24px; font-weight: 600; color: #2B6CB0;")

		subtitle = QLabel("Your aquarium companion, in one place.", page)
		subtitle.setAlignment(Qt.AlignCenter)
		subtitle.setStyleSheet("font-size: 14px; color: #555;")

		fish_select_button = QPushButton("Fish Select", page)
		fish_select_button.setFixedHeight(36)
		fish_select_button.clicked.connect(self._open_fish_select)

		compat_button = QPushButton("Compatibility", page)
		compat_button.setEnabled(False)
		compat_button.setFixedHeight(36)

		history_button = QPushButton("History", page)
		history_button.setFixedHeight(36)
		history_button.clicked.connect(self._open_history)

		aquariums_button = QPushButton("Aquariums", page)
		aquariums_button.setFixedHeight(40)
		aquariums_button.clicked.connect(self._open_aquarium_page)

		manage_button = QPushButton("Aquarium Management", page)
		manage_button.setFixedHeight(40)
		manage_button.clicked.connect(self._open_aquarium_management)

		layout.addStretch(1)
		layout.addWidget(title)
		layout.addWidget(subtitle)
		layout.addSpacing(16)
		layout.addWidget(fish_select_button)
		layout.addWidget(compat_button)
		layout.addWidget(history_button)
		layout.addWidget(aquariums_button)
		layout.addWidget(manage_button)
		layout.addStretch(1)

		return page

	def _open_aquarium_page(self) -> None:
		self.aquarium_window = AquariumPage()
		self.aquarium_window.setWindowTitle("Proprif Fish - Aquariums")
		self.aquarium_window.show()

	def _open_fish_select(self) -> None:
		if self.fish_select_window is None:
			self.fish_select_window = FishSelectWindow(parent=self)
		self.fish_select_window.show()

	def _open_history(self) -> None:
		if self.history_window is None:
			self.history_window = HistoryWindow(parent=self)
		self.history_window.show()

	def _open_aquarium_management(self) -> None:
		self.management_window = AquariumManagementPage()
		self.management_window.setWindowTitle("Proprif Fish - Aquarium Management")
		self.management_window.show()
