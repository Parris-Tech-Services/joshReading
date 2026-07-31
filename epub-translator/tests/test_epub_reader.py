"""Tests for EPUB reading."""

import pytest
import tempfile
from pathlib import Path
from zipfile import ZipFile

from epub_translator.epub.reader import EPUBReader


def create_minimal_epub(temp_path: Path) -> Path:
    """Create a minimal valid EPUB for testing."""
    epub_path = temp_path / "test.epub"
    
    with ZipFile(epub_path, 'w') as zf:
        # Mimetype (must be first, uncompressed)
        zf.writestr("mimetype", "application/epub+zip")
        
        # Container
        container_xml = """<?xml version="1.0" encoding="UTF-8"?>
<container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container">
    <rootfile full-path="OEBPS/content.opf" media-type="application/oebps-package+xml"/>
</container>"""
        zf.writestr("META-INF/container.xml", container_xml)
        
        # OPF (content.opf)
        opf_content = """<?xml version="1.0" encoding="UTF-8"?>
<package xmlns="http://www.idpf.org/2007/opf" version="3.0" unique-identifier="uuid_id">
    <metadata xmlns:dc="http://purl.org/dc/elements/1.1/">
        <dc:title>Test Book</dc:title>
        <dc:creator>Test Author</dc:creator>
        <dc:language>fr</dc:language>
        <dc:identifier id="uuid_id">test-uuid-123</dc:identifier>
    </metadata>
    <manifest>
        <item id="ch1" href="ch1.html" media-type="application/xhtml+xml"/>
    </manifest>
    <spine>
        <itemref idref="ch1"/>
    </spine>
</package>"""
        zf.writestr("OEBPS/content.opf", opf_content)
        
        # Chapter
        chapter_html = """<?xml version="1.0" encoding="UTF-8"?>
<html xmlns="http://www.w3.org/1999/xhtml">
<head><title>Chapter 1</title></head>
<body>
<h1>Chapitre 1</h1>
<p>Ceci est un texte de test.</p>
</body>
</html>"""
        zf.writestr("OEBPS/ch1.html", chapter_html)
    
    return epub_path


class TestEPUBReader:
    """Test EPUB reader."""

    def test_read_minimal_epub(self):
        """Should read minimal EPUB file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            epub_path = create_minimal_epub(Path(tmpdir))
            
            with EPUBReader(str(epub_path)) as reader:
                chapters = reader.get_chapters()
                assert len(chapters) > 0
                assert "title" in chapters[0]
                assert "content" in chapters[0]

    def test_read_metadata(self):
        """Should read EPUB metadata."""
        with tempfile.TemporaryDirectory() as tmpdir:
            epub_path = create_minimal_epub(Path(tmpdir))
            
            with EPUBReader(str(epub_path)) as reader:
                metadata = reader.get_metadata()
                assert metadata.get("title") == "Test Book"
                assert metadata.get("author") == "Test Author"
                assert metadata.get("language") == "fr"

    def test_file_hash(self):
        """Should generate consistent file hash."""
        with tempfile.TemporaryDirectory() as tmpdir:
            epub_path = create_minimal_epub(Path(tmpdir))
            
            with EPUBReader(str(epub_path)) as reader1:
                hash1 = reader1.get_file_hash()
            
            with EPUBReader(str(epub_path)) as reader2:
                hash2 = reader2.get_file_hash()
            
            assert hash1 == hash2
            assert len(hash1) == 64  # SHA256 hex length

    def test_nonexistent_file(self):
        """Should raise error for nonexistent file."""
        with pytest.raises(FileNotFoundError):
            EPUBReader("/nonexistent/path.epub")

    def test_drm_detection(self):
        """Should detect DRM."""
        with tempfile.TemporaryDirectory() as tmpdir:
            epub_path = Path(tmpdir) / "drm_test.epub"
            
            with ZipFile(epub_path, 'w') as zf:
                zf.writestr("mimetype", "application/epub+zip")
                zf.writestr("META-INF/container.xml", "<?xml version=\"1.0\"?><container/>")
                zf.writestr("META-INF/encryption.xml", "<?xml version=\"1.0\"?><encryption/>")
            
            with pytest.raises(ValueError, match="DRM"):
                EPUBReader(str(epub_path))

    def test_context_manager(self):
        """Should work as context manager."""
        with tempfile.TemporaryDirectory() as tmpdir:
            epub_path = create_minimal_epub(Path(tmpdir))
            
            with EPUBReader(str(epub_path)) as reader:
                assert reader.epub_path.exists()
            
            # After exiting context, zip should be closed
            assert not reader.zip_file or reader.zip_file.fp is None or reader.zip_file.fp.closed
