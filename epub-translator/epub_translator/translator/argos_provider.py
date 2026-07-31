"""Argos Translate provider for offline multi-language translation."""

import logging
from typing import Dict, List, Optional, Tuple

from .base import BaseTranslator

try:
    import argostranslate.package
    import argostranslate.translate
    ARGOS_AVAILABLE = True
except ImportError:
    ARGOS_AVAILABLE = False

logger = logging.getLogger(__name__)

# Language name mapping for display
LANGUAGE_NAMES = {
    "fr": "French",
    "es": "Spanish",
    "de": "German",
    "it": "Italian",
    "pt": "Portuguese",
    "ru": "Russian",
    "ja": "Japanese",
    "zh": "Chinese",
    "ko": "Korean",
    "ar": "Arabic",
    "hi": "Hindi",
    "nl": "Dutch",
    "pl": "Polish",
    "tr": "Turkish",
    "vi": "Vietnamese",
    "th": "Thai",
    "el": "Greek",
    "hu": "Hungarian",
    "cs": "Czech",
    "sv": "Swedish",
    "fi": "Finnish",
    "da": "Danish",
    "nb": "Norwegian",
    "en": "English",
}

# CJK (Chinese, Japanese, Korean) language codes
CJK_LANGUAGES = {"zh", "ja", "ko"}


class ArgosTranslator(BaseTranslator):
    """Offline translator using Argos Translate with multi-language support."""

    def __init__(self, source_language: str = "fr"):
        """
        Initialize Argos Translator.

        Args:
            source_language: Language code to translate from (e.g. "fr", "es")
        """
        if not ARGOS_AVAILABLE:
            raise ImportError(
                "argostranslate is not installed. "
                "Install it with: pip install argostranslate"
            )
        self.source_language = source_language
        self.installed = self._check_model_installed(source_language)

    def _check_model_installed(self, source_language: str) -> bool:
        """
        Check if X-to-English model is installed.

        Args:
            source_language: Language code to check

        Returns:
            True if model is installed, False otherwise
        """
        try:
            installed_packages = argostranslate.package.get_installed_packages()
            lang_name = LANGUAGE_NAMES.get(source_language, source_language)
            for package in installed_packages:
                if package.from_code == source_language and package.to_code == "en":
                    logger.info(f"{lang_name}-to-English model found")
                    return True
            logger.warning(f"{lang_name}-to-English model not found")
            return False
        except Exception as e:
            logger.error(f"Error checking for Argos model: {e}")
            return False

    @staticmethod
    def get_installed_languages() -> List[str]:
        """
        Get list of installed X→English language codes.

        Returns:
            List of language codes with X→English translation available
        """
        try:
            installed_packages = argostranslate.package.get_installed_packages()
            languages = []
            for package in installed_packages:
                if package.to_code == "en" and package.from_code not in languages:
                    languages.append(package.from_code)
            return sorted(languages)
        except Exception as e:
            logger.error(f"Error getting installed languages: {e}")
            return []

    @staticmethod
    def get_available_packages() -> List[Dict]:
        """
        Get list of all available X→English Argos packages (including installed).

        Returns:
            List of dicts with keys: code, name, size_mb, installed
        """
        try:
            argostranslate.package.update_package_index()
            available = argostranslate.package.get_available_packages()
            installed = argostranslate.package.get_installed_packages()
            
            installed_codes = set()
            for pkg in installed:
                if pkg.to_code == "en":
                    installed_codes.add(pkg.from_code)
            
            packages = []
            for pkg in available:
                if pkg.to_code == "en":
                    code = pkg.from_code
                    name = LANGUAGE_NAMES.get(code, code.upper())
                    size = getattr(pkg, "size", None)
                    packages.append({
                        "code": code,
                        "name": name,
                        "size_mb": size,
                        "installed": code in installed_codes,
                    })
            
            # Sort by name
            return sorted(packages, key=lambda x: x["name"])
        except Exception as e:
            logger.error(f"Error getting available packages: {e}")
            return []

    def is_model_installed(self) -> bool:
        """
        Check if the translation model is installed.

        Returns:
            True if model is available, False otherwise
        """
        return self.installed

    def install_model(self, source_language: str, on_progress: Optional[callable] = None) -> bool:
        """
        Download and install the X-to-English model.

        Args:
            source_language: Language code to install
            on_progress: Optional callback for progress updates

        Returns:
            True if installation successful, False otherwise
        """
        try:
            lang_name = LANGUAGE_NAMES.get(source_language, source_language)
            logger.info(f"Starting {lang_name} model download and installation...")
            argostranslate.package.update_package_index()
            packages = argostranslate.package.get_available_packages()
            
            package_to_install = None
            for package in packages:
                if package.from_code == source_language and package.to_code == "en":
                    package_to_install = package
                    break
            
            if package_to_install is None:
                logger.error(f"{lang_name}-to-English package not found in available packages")
                return False
            
            download_size_mb = getattr(package_to_install, "size", None)
            if download_size_mb:
                logger.info(f"Download size: ~{download_size_mb:.1f} MB")
            
            # Download the package file
            logger.info(f"Downloading {lang_name} model...")
            package_path = package_to_install.download()
            
            # Install from the downloaded file
            logger.info(f"Installing {lang_name} model from {package_path}...")
            argostranslate.package.install_from_path(package_path)
            
            self.source_language = source_language
            self.installed = True
            logger.info(f"{lang_name}-to-English model installed successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to install Argos model: {e}")
            return False

    def translate(self, text: str) -> str:
        """
        Translate text to English using Argos Translate.

        Args:
            text: Text to translate in source language

        Returns:
            English translation

        Raises:
            RuntimeError: If model is not installed or translation fails
        """
        if not self.installed:
            lang_name = LANGUAGE_NAMES.get(self.source_language, self.source_language)
            raise RuntimeError(
                f"{lang_name}-to-English model is not installed. "
                "Use install_model() first."
            )
        
        if not text or not text.strip():
            return text
        
        try:
            translated = argostranslate.translate.translate(text, self.source_language, "en")
            return translated
        except Exception as e:
            logger.error(f"Translation error: {e}")
            raise RuntimeError(f"Translation failed: {e}")

    def set_source_language(self, language_code: str) -> bool:
        """
        Change source language.

        Args:
            language_code: New source language code

        Returns:
            True if language model is installed, False otherwise
        """
        self.source_language = language_code
        self.installed = self._check_model_installed(language_code)
        return self.installed

    @staticmethod
    def is_cjk_language(language_code: str) -> bool:
        """
        Check if language is CJK (uses character-based chunking).

        Args:
            language_code: Language code to check

        Returns:
            True if language is Chinese, Japanese, or Korean
        """
        return language_code in CJK_LANGUAGES
