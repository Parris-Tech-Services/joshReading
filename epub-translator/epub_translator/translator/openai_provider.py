"""OpenAI translation provider (stub for future implementation)."""

from .base import BaseTranslator


class OpenAITranslator(BaseTranslator):
    """OpenAI translation provider (not implemented in v1)."""

    def translate(self, text: str) -> str:
        """
        Translate using OpenAI API.

        Args:
            text: French text to translate

        Raises:
            NotImplementedError: This provider is not implemented in v1
        """
        raise NotImplementedError(
            "OpenAI provider is not implemented in v1. "
            "Please use ArgosTranslator for offline translation."
        )
