"""Checkpoint system for resumable translation jobs."""

import json
import logging
from pathlib import Path
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


class CheckpointManager:
    """Manage translation checkpoints for resume capability."""

    CHECKPOINT_DIR = Path.home() / ".local" / "share" / "epub-translator"

    def __init__(self):
        """Initialize checkpoint manager."""
        self.CHECKPOINT_DIR.mkdir(parents=True, exist_ok=True)

    def _get_checkpoint_path(self, file_hash: str, language_code: str = "fr") -> Path:
        """Get path to checkpoint file for a given EPUB hash and language code."""
        # Use language code in filename for separation
        return self.CHECKPOINT_DIR / f"{file_hash}_{language_code}.json"

    def save_checkpoint(
        self,
        file_hash: str,
        completed_chapters: List[int],
        total_chapters: int,
        chapter_paths: List[str],
        translated_chapters: Dict[int, str],
        language_code: str = "fr",
    ) -> bool:
        """
        Save progress checkpoint.

        Args:
            file_hash: SHA-256 hash of input EPUB
            completed_chapters: List of chapter indices completed
            total_chapters: Total number of chapters
            chapter_paths: List of chapter file paths
            translated_chapters: Dict mapping chapter index to translated HTML
            language_code: Source language code (default "fr" for backwards compatibility)

        Returns:
            True if saved successfully
        """
        try:
            checkpoint = {
                "file_hash": file_hash,
                "language_code": language_code,
                "completed_chapters": completed_chapters,
                "total_chapters": total_chapters,
                "chapter_paths": chapter_paths,
                "translated_chapters": translated_chapters,
                "status": "in_progress",
            }
            
            checkpoint_path = self._get_checkpoint_path(file_hash, language_code)
            with open(checkpoint_path, "w") as f:
                json.dump(checkpoint, f, indent=2)
            
            logger.info(f"Checkpoint saved ({language_code}): {len(completed_chapters)}/{total_chapters} chapters")
            return True
        except Exception as e:
            logger.error(f"Error saving checkpoint: {e}")
            return False

    def load_checkpoint(self, file_hash: str, language_code: str = "fr") -> Optional[Dict]:
        """
        Load existing checkpoint if available.

        Args:
            file_hash: SHA-256 hash of input EPUB
            language_code: Source language code (default "fr" for backwards compatibility)

        Returns:
            Checkpoint dict if found, None otherwise
        """
        try:
            checkpoint_path = self._get_checkpoint_path(file_hash, language_code)
            if not checkpoint_path.exists():
                logger.info("No checkpoint found")
                return None
            
            with open(checkpoint_path, "r") as f:
                checkpoint = json.load(f)
            
            # Ensure language_code is in checkpoint (backwards compatibility)
            if "language_code" not in checkpoint:
                checkpoint["language_code"] = "fr"
            
            logger.info(f"Checkpoint loaded ({language_code}): {len(checkpoint['completed_chapters'])}/{checkpoint['total_chapters']} chapters")
            return checkpoint
        except Exception as e:
            logger.error(f"Error loading checkpoint: {e}")
            return None

    def cleanup_checkpoint(self, file_hash: str, language_code: str = "fr") -> bool:
        """
        Remove checkpoint after successful completion.

        Args:
            file_hash: SHA-256 hash of input EPUB
            language_code: Source language code

        Returns:
            True if cleaned up
        """
        try:
            checkpoint_path = self._get_checkpoint_path(file_hash, language_code)
            if checkpoint_path.exists():
                checkpoint_path.unlink()
                logger.info("Checkpoint cleaned up after successful translation")
            return True
        except Exception as e:
            logger.error(f"Error cleaning up checkpoint: {e}")
            return False

    def mark_checkpoint_complete(self, file_hash: str, language_code: str = "fr") -> bool:
        """
        Mark checkpoint as complete (before cleanup).

        Args:
            file_hash: SHA-256 hash of input EPUB
            language_code: Source language code

        Returns:
            True if marked successfully
        """
        try:
            checkpoint_path = self._get_checkpoint_path(file_hash, language_code)
            if checkpoint_path.exists():
                with open(checkpoint_path, "r") as f:
                    checkpoint = json.load(f)
                
                checkpoint["status"] = "complete"
                
                with open(checkpoint_path, "w") as f:
                    json.dump(checkpoint, f, indent=2)
                
                return True
            return False
        except Exception as e:
            logger.error(f"Error marking checkpoint complete: {e}")
            return False
