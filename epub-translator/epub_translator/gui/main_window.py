"""Main GUI window for EPUB Translator."""

import logging
import os
from pathlib import Path
from typing import Optional

from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import (
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QProgressBar,
    QTextEdit,
    QFileDialog,
    QMessageBox,
    QLineEdit,
    QFrame,
    QScrollArea,
    QComboBox,
)
from PySide6.QtGui import QIcon, QFont

from epub_translator.translator.argos_provider import ArgosTranslator, LANGUAGE_NAMES
from .worker import TranslationWorker
from .language_installer import LanguageInstallerDialog

logger = logging.getLogger(__name__)


class MainWindow(QMainWindow):
    """Main application window."""

    def __init__(self):
        """Initialize main window."""
        super().__init__()
        self.translator: Optional[ArgosTranslator] = None
        self.worker: Optional[TranslationWorker] = None
        self.input_file = ""
        self.output_file = ""
        self.source_language = "fr"
        
        self.setWindowTitle("EPUB Translator")
        self.setGeometry(100, 100, 900, 800)
        
        # Create all UI widgets first (including language_selector)
        self._create_ui()
        # Then initialize translator (may call _update_language_selector)
        self._init_translator()
        # Connect signals and populate UI
        self._connect_signals()
        self._update_language_selector()

    def _init_translator(self) -> None:
        """Initialize Argos Translator with default language."""
        try:
            installed_languages = ArgosTranslator.get_installed_languages()
            if not installed_languages:
                # Offer to install a language pack
                reply = QMessageBox.question(
                    self,
                    "No Translation Models Installed",
                    "No translation models are currently installed.\n\n"
                    "Would you like to install one now?",
                    QMessageBox.Yes | QMessageBox.No,
                )
                if reply == QMessageBox.Yes:
                    self._open_language_installer()
                return

            # Use first installed language (French preferred if available)
            if "fr" in installed_languages:
                self.source_language = "fr"
            else:
                self.source_language = installed_languages[0]

            self.translator = ArgosTranslator(self.source_language)
        except ImportError as e:
            QMessageBox.critical(
                self,
                "Error",
                f"Failed to initialize translator: {e}",
            )

    def _create_ui(self) -> None:
        """Create user interface."""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout()

        # Language selection section
        language_section = self._create_language_section()
        main_layout.addWidget(language_section)

        # File selection section
        file_section = self._create_file_section()
        main_layout.addWidget(file_section)

        # Translation controls
        controls = self._create_controls()
        main_layout.addWidget(controls)

        # Progress section
        progress_section = self._create_progress_section()
        main_layout.addWidget(progress_section)

        # Activity log
        log_label = QLabel("Activity Log:")
        log_font = QFont()
        log_font.setBold(True)
        log_label.setFont(log_font)
        main_layout.addWidget(log_label)

        self.log_display = QTextEdit()
        self.log_display.setReadOnly(True)
        self.log_display.setMaximumHeight(200)
        main_layout.addWidget(self.log_display)

        # Output controls
        output_controls = self._create_output_controls()
        main_layout.addWidget(output_controls)

        main_layout.addStretch()
        central_widget.setLayout(main_layout)

    def _connect_signals(self) -> None:
        """Connect all UI signals to slots."""
        # Language section signals
        self.language_selector.currentIndexChanged.connect(self._on_language_changed)
        self.install_language_btn.clicked.connect(self._open_language_installer)
        
        # File section signals
        self.browse_input_btn.clicked.connect(self._browse_input)
        self.browse_output_btn.clicked.connect(self._browse_output)
        
        # Control buttons signals
        self.start_btn.clicked.connect(self._start_translation)
        self.pause_btn.clicked.connect(self._pause_translation)
        self.resume_btn.clicked.connect(self._resume_translation)
        self.cancel_btn.clicked.connect(self._cancel_translation)
        
        # Output controls signals
        self.open_folder_btn.clicked.connect(self._open_output_folder)
        self.open_epub_btn.clicked.connect(self._open_translated_epub)

    def _create_language_section(self) -> QFrame:
        """Create language selection section."""
        frame = QFrame()
        layout = QHBoxLayout()

        layout.addWidget(QLabel("Source Language:"))
        
        self.language_selector = QComboBox()
        layout.addWidget(self.language_selector)

        layout.addStretch()

        self.install_language_btn = QPushButton("Install Language Pack")
        layout.addWidget(self.install_language_btn)

        frame.setLayout(layout)
        return frame

    def _update_language_selector(self) -> None:
        """Update language selector with installed languages."""
        installed = ArgosTranslator.get_installed_languages()
        
        self.language_selector.blockSignals(True)
        self.language_selector.clear()

        for lang_code in installed:
            lang_name = LANGUAGE_NAMES.get(lang_code, lang_code.upper())
            self.language_selector.addItem(lang_name, lang_code)

        # Select current language
        index = self.language_selector.findData(self.source_language)
        if index >= 0:
            self.language_selector.setCurrentIndex(index)

        self.language_selector.blockSignals(False)

    def _on_language_changed(self) -> None:
        """Handle language selector change."""
        old_language = self.source_language
        self.source_language = self.language_selector.currentData()
        
        if self.translator and self.translator.source_language != self.source_language:
            if not self.translator.set_source_language(self.source_language):
                QMessageBox.warning(
                    self,
                    "Model Not Installed",
                    f"The {LANGUAGE_NAMES.get(self.source_language, self.source_language)} model is not installed.\n\n"
                    "Click 'Install Language Pack' to download it.",
                )
                self.source_language = old_language
                self.language_selector.setCurrentData(old_language)
                return
        
        lang_name = LANGUAGE_NAMES.get(self.source_language, self.source_language)
        self.log_display.append(f"Language changed to: {lang_name}")

    def _open_language_installer(self) -> None:
        """Open language installer dialog."""
        dialog = LanguageInstallerDialog(self)
        dialog.exec()
        
        # Refresh language selector
        self._update_language_selector()

    def _create_file_section(self) -> QFrame:
        """Create file selection section."""
        frame = QFrame()
        layout = QVBoxLayout()

        # Input file
        input_layout = QHBoxLayout()
        lang_name = LANGUAGE_NAMES.get(self.source_language, self.source_language)
        input_layout.addWidget(QLabel(f"Input EPUB ({lang_name}):"))
        self.input_file_display = QLineEdit()
        self.input_file_display.setReadOnly(True)
        input_layout.addWidget(self.input_file_display)
        self.browse_input_btn = QPushButton("Browse...")
        input_layout.addWidget(self.browse_input_btn)
        layout.addLayout(input_layout)

        # Output folder
        output_layout = QHBoxLayout()
        output_layout.addWidget(QLabel("Output Folder:"))
        self.output_folder_display = QLineEdit()
        self.output_folder_display.setReadOnly(True)
        output_layout.addWidget(self.output_folder_display)
        self.browse_output_btn = QPushButton("Browse...")
        output_layout.addWidget(self.browse_output_btn)
        layout.addLayout(output_layout)

        frame.setLayout(layout)
        return frame

    def _create_controls(self) -> QFrame:
        """Create translation control buttons."""
        frame = QFrame()
        layout = QHBoxLayout()

        self.start_btn = QPushButton("Start Translation")
        layout.addWidget(self.start_btn)

        self.pause_btn = QPushButton("Pause")
        self.pause_btn.setEnabled(False)
        layout.addWidget(self.pause_btn)

        self.resume_btn = QPushButton("Resume")
        self.resume_btn.setEnabled(False)
        layout.addWidget(self.resume_btn)

        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.setEnabled(False)
        layout.addWidget(self.cancel_btn)

        frame.setLayout(layout)
        return frame

    def _create_progress_section(self) -> QFrame:
        """Create progress display section."""
        frame = QFrame()
        layout = QVBoxLayout()

        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        layout.addWidget(self.progress_bar)

        # Status text
        status_layout = QHBoxLayout()
        status_layout.addWidget(QLabel("Current Chapter:"))
        self.chapter_label = QLabel("-")
        chapter_font = QFont()
        chapter_font.setBold(True)
        self.chapter_label.setFont(chapter_font)
        status_layout.addWidget(self.chapter_label)
        status_layout.addStretch()
        layout.addLayout(status_layout)

        # Chapters completed
        info_layout = QHBoxLayout()
        info_layout.addWidget(QLabel("Chapters:"))
        self.chapters_label = QLabel("0 / 0")
        self.chapters_label.setFont(chapter_font)
        info_layout.addWidget(self.chapters_label)

        info_layout.addWidget(QLabel("Estimated Time:"))
        self.eta_label = QLabel("-")
        self.eta_label.setFont(chapter_font)
        info_layout.addWidget(self.eta_label)
        info_layout.addStretch()
        layout.addLayout(info_layout)

        frame.setLayout(layout)
        return frame

    def _create_output_controls(self) -> QFrame:
        """Create output folder and EPUB open buttons."""
        frame = QFrame()
        layout = QHBoxLayout()

        self.open_folder_btn = QPushButton("Open Output Folder")
        self.open_folder_btn.setEnabled(False)
        layout.addWidget(self.open_folder_btn)

        self.open_epub_btn = QPushButton("Open Translated EPUB")
        self.open_epub_btn.setEnabled(False)
        layout.addWidget(self.open_epub_btn)

        layout.addStretch()
        frame.setLayout(layout)
        return frame

    def _browse_input(self) -> None:
        """Browse for input EPUB file."""
        lang_name = LANGUAGE_NAMES.get(self.source_language, self.source_language)
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            f"Select {lang_name} EPUB",
            "",
            "EPUB Files (*.epub);;All Files (*)",
        )
        if file_path:
            self.input_file = file_path
            self.input_file_display.setText(file_path)

    def _browse_output(self) -> None:
        """Browse for output folder."""
        folder = QFileDialog.getExistingDirectory(
            self,
            "Select Output Folder",
        )
        if folder:
            self.output_file = folder
            self.output_folder_display.setText(folder)

    def _start_translation(self) -> None:
        """Start translation."""
        if not self.input_file:
            QMessageBox.warning(self, "Error", "Please select an input EPUB file")
            return

        if not self.output_file:
            QMessageBox.warning(self, "Error", "Please select an output folder")
            return

        if not self.translator or not self.translator.is_model_installed():
            QMessageBox.critical(
                self,
                "Error",
                "Translation model is not installed. Please install it first.",
            )
            return

        # Generate output file path
        input_name = Path(self.input_file).stem
        output_path = Path(self.output_file) / f"{input_name}_EN.epub"

        # Check if file exists
        if output_path.exists():
            reply = QMessageBox.question(
                self,
                "File Exists",
                f"Output file already exists:\n{output_path}\n\nOverwrite?",
                QMessageBox.Yes | QMessageBox.No,
            )
            if reply == QMessageBox.No:
                return

        # Start worker
        self.worker = TranslationWorker(
            self.input_file,
            str(output_path),
            self.translator,
            self.source_language,
        )

        self.worker.progress_updated.connect(self._on_progress)
        self.worker.status_changed.connect(self._on_status)
        self.worker.chapter_completed.connect(self._on_chapter_completed)
        self.worker.translation_finished.connect(self._on_translation_finished)
        self.worker.error_occurred.connect(self._on_error)

        # Update UI state
        self.start_btn.setEnabled(False)
        self.pause_btn.setEnabled(True)
        self.cancel_btn.setEnabled(True)
        self.browse_input_btn.setEnabled(False)
        self.browse_output_btn.setEnabled(False)
        self.language_selector.setEnabled(False)

        self.worker.start()
        lang_name = LANGUAGE_NAMES.get(self.source_language, self.source_language)
        self.statusBar().showMessage(f"Translation started ({lang_name})...")

    def _pause_translation(self) -> None:
        """Pause translation."""
        if self.worker:
            self.worker.pause()
            self.pause_btn.setEnabled(False)
            self.resume_btn.setEnabled(True)

    def _resume_translation(self) -> None:
        """Resume translation."""
        if self.worker:
            self.worker.resume()
            self.pause_btn.setEnabled(True)
            self.resume_btn.setEnabled(False)

    def _cancel_translation(self) -> None:
        """Cancel translation."""
        if self.worker:
            reply = QMessageBox.question(
                self,
                "Cancel Translation",
                "Are you sure you want to cancel? Progress will be saved.",
                QMessageBox.Yes | QMessageBox.No,
            )
            if reply == QMessageBox.Yes:
                self.worker.cancel()

    def _on_progress(self, percentage: int, chapter: str, completed: int, total: int, eta_seconds: float) -> None:
        """Handle progress update."""
        self.progress_bar.setValue(percentage)
        self.chapter_label.setText(chapter)
        self.chapters_label.setText(f"{completed} / {total}")

        if eta_seconds > 0:
            minutes = int(eta_seconds // 60)
            seconds = int(eta_seconds % 60)
            if minutes > 0:
                self.eta_label.setText(f"~{minutes}m {seconds}s (estimate)")
            else:
                self.eta_label.setText(f"~{seconds}s (estimate)")
        else:
            self.eta_label.setText("-")

    def _on_status(self, status: str) -> None:
        """Handle status message."""
        self.log_display.append(status)
        self.statusBar().showMessage(status)

    def _on_chapter_completed(self, chapter_name: str, idx: int) -> None:
        """Handle chapter completion."""
        self.log_display.append(f"✓ Completed: {chapter_name}")

    def _on_translation_finished(self, success: bool, message: str) -> None:
        """Handle translation completion."""
        self.log_display.append(f"\n{'='*50}")
        self.log_display.append(message)

        if success:
            QMessageBox.information(self, "Success", message)
            self.open_epub_btn.setEnabled(True)
            self.open_folder_btn.setEnabled(True)
        else:
            QMessageBox.warning(self, "Translation Complete", message)

        # Reset UI
        self.start_btn.setEnabled(True)
        self.pause_btn.setEnabled(False)
        self.resume_btn.setEnabled(False)
        self.cancel_btn.setEnabled(False)
        self.browse_input_btn.setEnabled(True)
        self.browse_output_btn.setEnabled(True)
        self.language_selector.setEnabled(True)

        self.statusBar().showMessage("Ready")

    def _on_error(self, error_msg: str) -> None:
        """Handle error."""
        self.log_display.append(f"\n❌ ERROR: {error_msg}")
        QMessageBox.critical(self, "Error", error_msg)

        # Reset UI
        self.start_btn.setEnabled(True)
        self.pause_btn.setEnabled(False)
        self.resume_btn.setEnabled(False)
        self.cancel_btn.setEnabled(False)
        self.browse_input_btn.setEnabled(True)
        self.browse_output_btn.setEnabled(True)
        self.language_selector.setEnabled(True)

    def _open_output_folder(self) -> None:
        """Open output folder in file manager."""
        if self.output_file:
            os.system(f"xdg-open '{self.output_file}'")

    def _open_translated_epub(self) -> None:
        """Open translated EPUB in default ebook reader."""
        input_name = Path(self.input_file).stem
        output_path = Path(self.output_file) / f"{input_name}_EN.epub"
        if output_path.exists():
            os.system(f"xdg-open '{output_path}'")

    def closeEvent(self, event) -> None:
        """Handle window close."""
        if self.worker and self.worker.isRunning():
            reply = QMessageBox.question(
                self,
                "Translation In Progress",
                "Translation is still running. Exit anyway?",
                QMessageBox.Yes | QMessageBox.No,
            )
            if reply == QMessageBox.No:
                event.ignore()
                return
            self.worker.cancel()
            self.worker.wait()

        event.accept()
