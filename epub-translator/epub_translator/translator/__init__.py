"""Translation providers for EPUB Translator."""

from .base import BaseTranslator
from .argos_provider import ArgosTranslator

__all__ = ["BaseTranslator", "ArgosTranslator"]
