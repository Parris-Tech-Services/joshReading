"""LibreTranslate provider (stub for future implementation)."""

from .base import BaseTranslator


class LibreTranslateTranslator(BaseTranslator):
    """LibreTranslate provider (not implemented in v1)."""

    def translate(self, text: str) -> str:
        """
        Translate using LibreTranslate API.

        Args:
            text: French text to translate

        Raises:
            NotImplementedError: This provider is not implemented in v1
        """
        raise NotImplementedError(
            "LibreTranslate provider is not implemented in v1. "
            "Please use ArgosTranslator for offline translation."
        )
