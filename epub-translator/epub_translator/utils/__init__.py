"""Utilities for text chunking and processing."""

import logging
import re
import unicodedata
from typing import List

logger = logging.getLogger(__name__)

# CJK character ranges
CJK_RANGES = [
    (0x4E00, 0x9FFF),    # CJK Unified Ideographs
    (0x3040, 0x309F),    # Hiragana
    (0x30A0, 0x30FF),    # Katakana
    (0xAC00, 0xD7AF),    # Hangul Syllables
]


def is_cjk_char(char: str) -> bool:
    """Check if character is CJK (Chinese, Japanese, Korean)."""
    code = ord(char)
    for start, end in CJK_RANGES:
        if start <= code <= end:
            return True
    return False


def has_cjk_content(text: str) -> bool:
    """Check if text contains CJK characters."""
    return any(is_cjk_char(char) for char in text)


def chunk_text(text: str, max_chunk_size: int = 500, is_cjk: bool = False) -> List[str]:
    """
    Split text into chunks under max_chunk_size characters.

    For European languages:
    - Text under 500 chars is not split
    - Text over 500 chars splits at sentence boundaries (. ? !)
    - Never split mid-word
    - Preserve whitespace sensibly
    - Do not join separate paragraphs

    For CJK languages:
    - Split at 300 character boundaries (CJK doesn't use spaces)
    - Never split mid-character

    Args:
        text: Text to chunk
        max_chunk_size: Maximum chunk size in characters (default 500)
        is_cjk: If True, use CJK character-based chunking (300 chars)

    Returns:
        List of text chunks
    """
    if not text or not text.strip():
        return []

    # Auto-detect CJK if not specified
    if not is_cjk and has_cjk_content(text):
        is_cjk = True

    # CJK chunking: character-based, not sentence-based
    if is_cjk:
        cjk_max_size = min(max_chunk_size, 300)
        chunks = []
        current_chunk = ""
        
        for char in text:
            if len(current_chunk) >= cjk_max_size:
                if current_chunk.strip():
                    chunks.append(current_chunk.strip())
                current_chunk = char
            else:
                current_chunk += char
        
        if current_chunk.strip():
            chunks.append(current_chunk.strip())
        
        logger.debug(f"Chunked CJK text into {len(chunks)} chunks")
        return chunks if chunks else []

    # European language chunking: sentence-based
    if len(text) <= max_chunk_size:
        return [text]

    chunks = []
    current_chunk = ""

    # Split by sentences using regex
    # Match sentence-ending punctuation followed by space(s)
    sentences = re.split(r'([.!?]\s+)', text)

    i = 0
    while i < len(sentences):
        sentence = sentences[i]
        
        # Skip empty strings
        if not sentence or not sentence.strip():
            i += 1
            continue

        # Check if this is a sentence boundary marker (. ? ! followed by space)
        is_boundary = re.match(r'^[.!?]\s+$', sentence)

        # If current chunk + next sentence exceeds max size
        if current_chunk and len(current_chunk) + len(sentence) > max_chunk_size:
            # Save current chunk and start new one
            if current_chunk.strip():
                chunks.append(current_chunk.strip())
            current_chunk = sentence if not is_boundary else ""
        else:
            current_chunk += sentence

        i += 1

    # Add remaining text
    if current_chunk.strip():
        chunks.append(current_chunk.strip())

    # Ensure no empty chunks
    chunks = [c for c in chunks if c.strip()]

    if not chunks:
        # Fallback: if no chunks were created, return original text
        return [text] if text.strip() else []

    logger.debug(f"Chunked text into {len(chunks)} chunks")
    return chunks
