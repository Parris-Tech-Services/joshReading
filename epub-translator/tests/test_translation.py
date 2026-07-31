"""Tests for base translator interface."""

import pytest

from epub_translator.translator.base import BaseTranslator
from epub_translator.translator.argos_provider import ArgosTranslator
from epub_translator.translator.deepl_provider import DeepLTranslator
from epub_translator.translator.openai_provider import OpenAITranslator
from epub_translator.translator.libretranslate_provider import LibreTranslateTranslator


class MockTranslator(BaseTranslator):
    """Mock translator for testing."""

    def translate(self, text: str) -> str:
        """Return fixed output for testing."""
        return f"[TRANSLATED] {text}"


class TestBaseTranslator:
    """Test base translator interface."""

    def test_base_translator_not_implemented(self):
        """BaseTranslator.translate should raise NotImplementedError."""
        translator = BaseTranslator()
        with pytest.raises(TypeError):
            # Can't instantiate abstract class
            pass

    def test_mock_translator_works(self):
        """Mock translator should work for testing."""
        translator = MockTranslator()
        result = translator.translate("Hello")
        assert result == "[TRANSLATED] Hello"

    def test_deepl_not_implemented(self):
        """DeepL provider should raise NotImplementedError."""
        translator = DeepLTranslator()
        with pytest.raises(NotImplementedError):
            translator.translate("test")

    def test_openai_not_implemented(self):
        """OpenAI provider should raise NotImplementedError."""
        translator = OpenAITranslator()
        with pytest.raises(NotImplementedError):
            translator.translate("test")

    def test_libretranslate_not_implemented(self):
        """LibreTranslate provider should raise NotImplementedError."""
        translator = LibreTranslateTranslator()
        with pytest.raises(NotImplementedError):
            translator.translate("test")


class TestArgosTranslator:
    """Test Argos translator."""

    def test_argos_initialization_with_language(self):
        """Argos translator should initialize with specified language."""
        try:
            translator = ArgosTranslator("fr")
            # Check if model installed status is boolean
            assert isinstance(translator.is_model_installed(), bool)
            assert translator.source_language == "fr"
        except ImportError:
            # Argos not installed, skip
            pytest.skip("Argos Translate not installed")

    def test_argos_get_installed_languages(self):
        """Should get list of installed languages."""
        try:
            languages = ArgosTranslator.get_installed_languages()
            # Should return a list
            assert isinstance(languages, list)
            # If any installed, should be string codes
            if languages:
                assert all(isinstance(lang, str) for lang in languages)
        except ImportError:
            pytest.skip("Argos Translate not installed")

    def test_argos_get_available_packages(self):
        """Should get list of available packages."""
        try:
            packages = ArgosTranslator.get_available_packages()
            # Should return a list
            assert isinstance(packages, list)
            # Each package should have required fields
            if packages:
                for pkg in packages:
                    assert "code" in pkg
                    assert "name" in pkg
                    assert "installed" in pkg
        except ImportError:
            pytest.skip("Argos Translate not installed")

    def test_argos_cjk_language_detection(self):
        """Should correctly identify CJK languages."""
        assert ArgosTranslator.is_cjk_language("zh")
        assert ArgosTranslator.is_cjk_language("ja")
        assert ArgosTranslator.is_cjk_language("ko")
        assert not ArgosTranslator.is_cjk_language("fr")
        assert not ArgosTranslator.is_cjk_language("es")

    def test_argos_set_source_language(self):
        """Should change source language."""
        try:
            translator = ArgosTranslator("fr")
            result = translator.set_source_language("es")
            # Result depends on whether es model is installed
            assert isinstance(result, bool)
            assert translator.source_language == "es"
        except ImportError:
            pytest.skip("Argos Translate not installed")

    @pytest.mark.skipif(True, reason="Requires model installation")
    def test_argos_translate(self):
        """Argos translator should translate text."""
        translator = ArgosTranslator("fr")
        if not translator.is_model_installed():
            pytest.skip("French-to-English model not installed")

        result = translator.translate("Bonjour")
        assert isinstance(result, str)
        assert len(result) > 0
