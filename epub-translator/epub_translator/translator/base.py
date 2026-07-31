"""Base translator interface for pluggable translation providers."""

from abc import ABC, abstractmethod


class BaseTranslator(ABC):
    """Abstract base class for translation providers."""

    @abstractmethod
    def translate(self, text: str) -> str:
        """
        Translate text from French to English.

        Args:
            text: French text to translate

        Returns:
            English translation

        Raises:
            NotImplementedError: If the method is not implemented by subclass
        """
        ...
