"""Main window UI for the desktop app."""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLabel, QMainWindow, QPushButton, QVBoxLayout, QWidget


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

		buttons = []
		for label in ("Fish List", "Compatibility", "History", "Aquariums"):
			button = QPushButton(label, page)
			button.setEnabled(False)
			button.setFixedHeight(36)
			buttons.append(button)

		layout.addStretch(1)
		layout.addWidget(title)
		layout.addWidget(subtitle)
		layout.addSpacing(16)
		for button in buttons:
			layout.addWidget(button)
		layout.addStretch(1)

		return page