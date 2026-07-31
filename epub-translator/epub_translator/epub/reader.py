"""EPUB file handling - reading, parsing, and structure preservation."""

import hashlib
import logging
import os
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from zipfile import ZipFile

from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

# XML namespaces used in EPUB files
NAMESPACES = {
    "container": "urn:oasis:names:tc:opendocument:xmlns:container",
    "opf": "http://www.idpf.org/2007/opf",
    "ncx": "http://www.daisy.org/z3986/2005/ncx/",
    "xhtml": "http://www.w3.org/1999/xhtml",
    "epub": "http://www.idpf.org/2007/ops",
}


class EPUBReader:
    """Read and parse EPUB files while preserving structure."""

    def __init__(self, epub_path: str):
        """
        Initialize EPUB reader.

        Args:
            epub_path: Path to the EPUB file

        Raises:
            FileNotFoundError: If EPUB file doesn't exist
            ValueError: If file is not a valid EPUB or has DRM
        """
        self.epub_path = Path(epub_path)
        if not self.epub_path.exists():
            raise FileNotFoundError(f"EPUB file not found: {epub_path}")

        self._validate_and_extract()

    def _validate_and_extract(self) -> None:
        """Extract and validate EPUB file."""
        try:
            self.zip_file = ZipFile(self.epub_path, 'r')
            # Check for DRM
            if self._has_drm():
                raise ValueError(
                    "This EPUB file contains DRM (encryption). "
                    "epub-translator only supports DRM-free files. "
                    "Please use a DRM-free version of the book."
                )
        except Exception as e:
            if "DRM" in str(e):
                raise
            raise ValueError(f"Invalid EPUB file: {e}")

    def _has_drm(self) -> bool:
        """
        Check if EPUB contains DRM by looking for encryption.xml.

        Returns:
            True if encryption.xml found, False otherwise
        """
        try:
            encryption_path = "META-INF/encryption.xml"
            if encryption_path in self.zip_file.namelist():
                logger.warning("DRM encryption detected in EPUB")
                return True
            return False
        except Exception as e:
            logger.debug(f"Error checking for DRM: {e}")
            return False

    def get_file_hash(self) -> str:
        """
        Get SHA-256 hash of EPUB file for checkpoint identification.

        Returns:
            Hex-encoded SHA-256 hash
        """
        sha256_hash = hashlib.sha256()
        with open(self.epub_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()

    def _get_opf_path(self) -> str:
        """Get path to OPF (package) file from container.xml."""
        try:
            container_xml = self.zip_file.read("META-INF/container.xml")
            root = ET.fromstring(container_xml)
            rootfile = root.find(
                ".//container:rootfile",
                NAMESPACES
            )
            if rootfile is not None:
                return rootfile.get("full-path", "content.opf")
            return "content.opf"
        except Exception as e:
            logger.warning(f"Could not parse container.xml: {e}, using default path")
            return "content.opf"

    def _get_spine_order(self) -> List[str]:
        """Get chapter files in spine order from OPF."""
        try:
            opf_path = self._get_opf_path()
            opf_content = self.zip_file.read(opf_path)
            root = ET.fromstring(opf_content)
            spine = root.find(".//opf:spine", NAMESPACES)
            if spine is None:
                logger.warning("No spine found in OPF")
                return []

            chapter_ids = []
            for itemref in spine.findall("opf:itemref", NAMESPACES):
                idref = itemref.get("idref")
                if idref:
                    chapter_ids.append(idref)

            return chapter_ids
        except Exception as e:
            logger.error(f"Error reading spine: {e}")
            return []

    def _get_chapter_path_from_id(self, chapter_id: str) -> Optional[str]:
        """Get file path for a chapter ID from the manifest."""
        try:
            opf_path = self._get_opf_path()
            opf_content = self.zip_file.read(opf_path)
            root = ET.fromstring(opf_content)
            manifest = root.find(".//opf:manifest", NAMESPACES)
            if manifest is None:
                return None

            for item in manifest.findall("opf:item", NAMESPACES):
                if item.get("id") == chapter_id:
                    href = item.get("href")
                    if href:
                        # Resolve relative paths
                        base_dir = Path(opf_path).parent
                        return str(base_dir / href).replace("\\", "/")
            return None
        except Exception as e:
            logger.error(f"Error reading manifest: {e}")
            return None

    def get_chapters(self) -> List[Dict]:
        """
        Get list of chapters with their content.

        Returns:
            List of dicts with keys: id, title, path, content, raw_html
        """
        chapters = []
        spine_ids = self._get_spine_order()

        for idx, chapter_id in enumerate(spine_ids):
            chapter_path = self._get_chapter_path_from_id(chapter_id)
            if not chapter_path:
                logger.warning(f"Could not find path for chapter {chapter_id}")
                continue

            try:
                content = self.zip_file.read(chapter_path).decode("utf-8")
                soup = BeautifulSoup(content, "html.parser")
                
                # Extract title
                title = soup.find("h1")
                if title:
                    title = title.get_text().strip()
                else:
                    title = f"Chapter {idx + 1}"

                chapters.append({
                    "id": chapter_id,
                    "title": title,
                    "path": chapter_path,
                    "content": str(soup),
                    "raw_html": content,
                })
            except Exception as e:
                logger.error(f"Error reading chapter {chapter_path}: {e}")

        return chapters

    def get_metadata(self) -> Dict:
        """
        Extract EPUB metadata (title, author, language, etc.).

        Returns:
            Dict with metadata
        """
        try:
            opf_path = self._get_opf_path()
            opf_content = self.zip_file.read(opf_path)
            root = ET.fromstring(opf_content)
            
            metadata = root.find(".//opf:metadata", NAMESPACES)
            if metadata is None:
                return {}

            result = {}
            
            # Dublin Core elements
            dc_ns = {"dc": "http://purl.org/dc/elements/1.1/"}
            
            title_elem = metadata.find("dc:title", dc_ns)
            if title_elem is not None:
                result["title"] = title_elem.text

            author_elem = metadata.find("dc:creator", dc_ns)
            if author_elem is not None:
                result["author"] = author_elem.text

            language_elem = metadata.find("dc:language", dc_ns)
            if language_elem is not None:
                result["language"] = language_elem.text

            # Get unique ID
            unique_id = root.get("unique-identifier")
            if unique_id:
                for item in root.findall(".//opf:identifier", NAMESPACES):
                    if item.get("id") == unique_id:
                        result["unique_id"] = item.text
                        break

            return result
        except Exception as e:
            logger.error(f"Error reading metadata: {e}")
            return {}

    def get_all_files(self) -> Dict[str, bytes]:
        """
        Get all files from EPUB for structure preservation.

        Returns:
            Dict mapping file paths to their contents
        """
        return {name: self.zip_file.read(name) for name in self.zip_file.namelist()}

    def close(self) -> None:
        """Close EPUB file."""
        if hasattr(self, 'zip_file'):
            self.zip_file.close()

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
