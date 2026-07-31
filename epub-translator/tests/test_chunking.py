"""Tests for text chunking functionality."""

import pytest

from epub_translator.utils import chunk_text, has_cjk_content, is_cjk_char


class TestChunking:
    """Test text chunking logic."""

    def test_empty_text(self):
        """Empty string should return empty list."""
        assert chunk_text("") == []
        assert chunk_text("   ") == []

    def test_short_text_not_split(self):
        """Text under 500 chars should not be split."""
        text = "This is a short sentence. " * 5
        assert len(text) < 500
        result = chunk_text(text)
        assert len(result) == 1
        assert result[0] == text.strip()

    def test_long_text_splits_at_sentences(self):
        """Text over 500 chars should split at sentence boundaries."""
        # Create text > 500 chars
        sentence = "This is a test sentence. " * 30  # ~750 chars
        assert len(sentence) > 500
        
        result = chunk_text(sentence)
        assert len(result) > 1
        
        # Each chunk should be under 500 chars
        for chunk in result:
            assert len(chunk) <= 500

    def test_split_at_period(self):
        """Should split at periods."""
        text = "First sentence. " * 40  # ~640 chars
        result = chunk_text(text)
        assert len(result) >= 2
        assert all(chunk.endswith(".") or "." not in chunk for chunk in result)

    def test_split_at_question_mark(self):
        """Should split at question marks."""
        text = "Is this a question? " * 30  # ~600 chars
        result = chunk_text(text)
        assert len(result) >= 2

    def test_split_at_exclamation(self):
        """Should split at exclamation marks."""
        text = "This is important! " * 30  # ~570 chars
        result = chunk_text(text)
        assert len(result) >= 2

    def test_no_empty_chunks(self):
        """Should not produce empty chunks."""
        text = "Sentence one. Sentence two. " * 20
        result = chunk_text(text)
        assert all(chunk.strip() for chunk in result)

    def test_preserves_whitespace(self):
        """Should preserve reasonable whitespace."""
        text = "First sentence.  Second sentence." * 20
        result = chunk_text(text)
        # Chunks should not have excessive whitespace
        assert not any("  " in chunk for chunk in result)

    def test_custom_max_size(self):
        """Should respect custom max chunk size."""
        text = "A " * 200  # ~400 chars
        result = chunk_text(text, max_chunk_size=100)
        # With smaller max size, should create more chunks
        assert all(len(chunk) <= 100 for chunk in result)

    def test_cjk_detection(self):
        """Should detect CJK content."""
        chinese_text = "这是一个测试。" * 50  # Chinese text repeated
        assert has_cjk_content(chinese_text)
        
        english_text = "This is a test. " * 50
        assert not has_cjk_content(english_text)

    def test_cjk_character_detection(self):
        """Should identify CJK characters."""
        # Chinese character
        assert is_cjk_char("中")
        # Japanese hiragana
        assert is_cjk_char("あ")
        # Japanese katakana
        assert is_cjk_char("ア")
        # Korean hangul
        assert is_cjk_char("한")
        # English letter
        assert not is_cjk_char("a")

    def test_cjk_chunking(self):
        """Should chunk CJK text by character count."""
        # Chinese text (no spaces between words)
        chinese_text = "这是一个很长的测试文本。" * 30  # ~360 characters
        result = chunk_text(chinese_text, is_cjk=True)
        
        # Should create multiple chunks
        assert len(result) > 1
        
        # Each chunk should be <= 300 chars (CJK limit)
        for chunk in result:
            assert len(chunk) <= 300

    def test_auto_detect_cjk(self):
        """Should auto-detect CJK without explicit flag."""
        chinese_text = "这是测试。" * 50
        # Call without is_cjk flag - should auto-detect
        result = chunk_text(chinese_text)
        
        # Should still chunk properly even without explicit flag
        assert len(result) > 0
        assert all(chunk.strip() for chunk in result)
