"""Language package installer dialog."""

import logging
from typing import Dict, List, Optional

from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QProgressDialog,
)

logger = logging.getLogger(__name__)


class LanguageInstallWorker(QThread):
    """Worker thread for installing language packages."""

    finished = Signal(bool, str)  # success, message
    progress = Signal(str)  # status message

    def __init__(self, package_info: Dict):
        """
        Initialize worker.

        Args:
            package_info: Dict with 'code', 'name', 'size_mb' keys
        """
        super().__init__()
        self.package_info = package_info

    def run(self):
        """Execute installation in background."""
        try:
            import argostranslate.package

            self.progress.emit(f"Downloading {self.package_info['name']}...")
            argostranslate.package.update_package_index()
            packages = argostranslate.package.get_available_packages()

            package_to_install = None
            for pkg in packages:
                if pkg.from_code == self.package_info["code"] and pkg.to_code == "en":
                    package_to_install = pkg
                    break

            if package_to_install is None:
                self.finished.emit(False, f"Package {self.package_info['name']} not found")
                return

            self.progress.emit(f"Installing {self.package_info['name']}...")
            # Download the package
            package_path = package_to_install.download()
            # Install from the downloaded file
            argostranslate.package.install_from_path(package_path)
            self.progress.emit(f"✓ {self.package_info['name']} installed successfully")
            self.finished.emit(True, f"{self.package_info['name']} installed successfully!")

        except Exception as e:
            logger.error(f"Installation error: {e}")
            self.finished.emit(False, f"Installation failed: {e}")


class LanguageInstallerDialog(QDialog):
    """Dialog for installing language packages."""

    def __init__(self, parent=None):
        """Initialize dialog."""
        super().__init__(parent)
        self.setWindowTitle("Install Language Pack")
        self.setGeometry(100, 100, 600, 400)
        self.selected_package: Optional[Dict] = None
        self.installer_worker: Optional[LanguageInstallWorker] = None

        self._create_ui()
        self._load_packages()

    def _create_ui(self) -> None:
        """Create user interface."""
        layout = QVBoxLayout()

        # Title
        title = QLabel("Available Language Packs for Translation to English")
        title_font = title.font()
        title_font.setBold(True)
        title.setFont(title_font)
        layout.addWidget(title)

        # Package list
        self.package_list = QListWidget()
        self.package_list.itemDoubleClicked.connect(self._on_install_clicked)
        layout.addWidget(self.package_list)

        # Buttons
        buttons_layout = QHBoxLayout()
        
        self.install_btn = QPushButton("Install Selected")
        self.install_btn.clicked.connect(self._on_install_clicked)
        self.install_btn.setEnabled(False)
        buttons_layout.addWidget(self.install_btn)

        buttons_layout.addStretch()

        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.reject)
        buttons_layout.addWidget(close_btn)

        layout.addLayout(buttons_layout)
        self.setLayout(layout)

    def _load_packages(self) -> None:
        """Load available packages from Argos Translate."""
        try:
            from epub_translator.translator.argos_provider import ArgosTranslator

            packages = ArgosTranslator.get_available_packages()
            self.packages = packages

            for pkg in packages:
                display_text = f"{pkg['name']}"
                if pkg["size_mb"]:
                    display_text += f" (~{pkg['size_mb']:.1f} MB)"
                if pkg["installed"]:
                    display_text += " ✓ Installed"

                item = QListWidgetItem(display_text)
                item.setData(Qt.UserRole, pkg["code"])
                
                # Disable installed packages
                if pkg["installed"]:
                    item.setFlags(item.flags() & ~Qt.ItemIsEnabled)

                self.package_list.addItem(item)

        except Exception as e:
            logger.error(f"Error loading packages: {e}")
            QMessageBox.critical(self, "Error", f"Failed to load packages: {e}")

    def _on_install_clicked(self) -> None:
        """Handle install button click."""
        current_item = self.package_list.currentItem()
        if not current_item or not current_item.flags() & Qt.ItemIsEnabled:
            QMessageBox.warning(self, "No Selection", "Please select a language pack to install")
            return

        code = current_item.data(Qt.UserRole)
        package = next((p for p in self.packages if p["code"] == code), None)
        if not package:
            return

        self.selected_package = package

        # Create progress dialog
        progress = QProgressDialog(
            f"Installing {package['name']}...",
            "Cancel",
            0,
            0,
            self,
        )
        progress.setWindowModality(Qt.WindowModal)
        progress.setAutoClose(False)
        progress.setCancelButton(None)

        # Start installation
        self.installer_worker = LanguageInstallWorker(package)
        self.installer_worker.progress.connect(
            lambda msg: progress.setLabelText(msg)
        )
        self.installer_worker.finished.connect(
            lambda success, msg: self._on_installation_finished(success, msg, progress)
        )
        self.installer_worker.start()

    def _on_installation_finished(
        self, success: bool, message: str, progress: QProgressDialog
    ) -> None:
        """Handle installation completion."""
        progress.close()

        if success:
            QMessageBox.information(
                self,
                "Success",
                message,
            )
            # Reload packages to show installed status
            self.package_list.clear()
            self._load_packages()
        else:
            QMessageBox.critical(
                self,
                "Error",
                message,
            )

    def get_selected_package(self) -> Optional[Dict]:
        """Get the selected package for installation."""
        return self.selected_package
