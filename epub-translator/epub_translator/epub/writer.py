"""EPUB file writing - create translated EPUB with preserved structure."""

import logging
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Dict, List, Optional
from zipfile import ZipFile, ZIP_DEFLATED

from bs4 import BeautifulSoup, NavigableString, Tag

from .reader import NAMESPACES

logger = logging.getLogger(__name__)


class EPUBWriter:
    """Write translated EPUB files while preserving structure."""

    def __init__(self, output_path: str):
        """
        Initialize EPUB writer.

        Args:
            output_path: Path where translated EPUB will be written
        """
        self.output_path = Path(output_path)
        self.output_path.parent.mkdir(parents=True, exist_ok=True)

    def create_translated_epub(
        self,
        original_epub_path: str,
        chapters_content: List[Dict],
        metadata_updates: Optional[Dict] = None,
    ) -> None:
        """
        Create a new EPUB with translated content.

        Args:
            original_epub_path: Path to original EPUB
            chapters_content: List of dicts with chapter info and translated content
            metadata_updates: Optional updates to metadata (e.g. language)

        Raises:
            Exception: If writing fails
        """
        try:
            # Open original EPUB for reading structure
            with ZipFile(original_epub_path, 'r') as original_zip:
                all_files = {
                    name: original_zip.read(name)
                    for name in original_zip.namelist()
                }

            # Create new EPUB
            with ZipFile(self.output_path, 'w', ZIP_DEFLATED) as new_zip:
                # Copy all files, replacing translated chapters
                for file_path, content in all_files.items():
                    # Check if this is a chapter that was translated
                    skip = False
                    for chapter in chapters_content:
                        if file_path == chapter.get("path"):
                            # Write translated content
                            new_zip.writestr(file_path, chapter["translated_html"])
                            skip = True
                            break

                    if not skip:
                        # Handle metadata updates
                        if file_path.startswith("META-INF/") or file_path == "content.opf":
                            if metadata_updates and file_path == "content.opf":
                                content = self._update_opf_metadata(
                                    content, metadata_updates
                                )
                        
                        new_zip.writestr(file_path, content)

            logger.info(f"Translated EPUB written to {self.output_path}")

        except Exception as e:
            logger.error(f"Error creating translated EPUB: {e}")
            raise

    def _update_opf_metadata(self, opf_content: bytes, updates: Dict) -> bytes:
        """
        Update OPF metadata (language, etc).

        Args:
            opf_content: Original OPF content as bytes
            updates: Dict with metadata updates

        Returns:
            Updated OPF content as bytes
        """
        try:
            root = ET.fromstring(opf_content)
            metadata = root.find(".//opf:metadata", NAMESPACES)
            
            if metadata is not None and "language" in updates:
                # Update language to English
                dc_ns = "{http://purl.org/dc/elements/1.1/}"
                lang_elem = metadata.find(f"{dc_ns}language")
                if lang_elem is not None:
                    lang_elem.text = "en"
                else:
                    # Create language element if it doesn't exist
                    lang_elem = ET.Element(f"{dc_ns}language")
                    lang_elem.text = "en"
                    metadata.append(lang_elem)

            # Return as bytes
            return ET.tostring(root, encoding="utf-8")

        except Exception as e:
            logger.warning(f"Could not update OPF metadata: {e}")
            return opf_content

    @staticmethod
    def translate_html_content(
        html_content: str,
        translator_func,
    ) -> str:
        """
        Translate text nodes in HTML while preserving structure.

        Args:
            html_content: HTML content to translate
            translator_func: Function that takes text and returns translation

        Returns:
            HTML with translated text
        """
        try:
            soup = BeautifulSoup(html_content, "html.parser")
            
            # Tags to skip (don't translate their content)
            skip_tags = {"script", "style", "code", "pre", "math", "svg"}
            
            def translate_recursive(element):
                """Recursively translate text nodes."""
                if isinstance(element, NavigableString):
                    # Don't translate if it's code or script
                    if element.parent and element.parent.name in skip_tags:
                        return
                    
                    text = str(element).strip()
                    if text:
                        try:
                            translated = translator_func(text)
                            element.replace_with(translated)
                        except Exception as e:
                            logger.warning(f"Failed to translate: {text[:50]}... - {e}")
                else:
                    # It's a tag
                    if element.name not in skip_tags:
                        # Process children
                        for child in list(element.children):
                            translate_recursive(child)

            translate_recursive(soup)
            return str(soup)

        except Exception as e:
            logger.error(f"Error translating HTML: {e}")
            return html_content
