"""Tests for checkpoint manager."""

import json
import tempfile
from pathlib import Path

import pytest

from epub_translator.checkpoint import CheckpointManager


class TestCheckpointManager:
    """Test checkpoint manager."""

    def setup_method(self):
        """Set up test fixtures."""
        self.manager = CheckpointManager()
        self.test_hash = "abc123def456"

    def teardown_method(self):
        """Clean up after tests."""
        checkpoint_path = self.manager._get_checkpoint_path(self.test_hash)
        if checkpoint_path.exists():
            checkpoint_path.unlink()

    def test_checkpoint_directory_created(self):
        """Checkpoint directory should be created."""
        assert self.manager.CHECKPOINT_DIR.exists()

    def test_save_checkpoint(self):
        """Should save checkpoint to file."""
        chapters = [0, 1, 2]
        total = 10
        paths = ["ch1.html", "ch2.html", "ch3.html"]
        translated = {0: "<p>Translated 1</p>", 1: "<p>Translated 2</p>"}

        success = self.manager.save_checkpoint(
            self.test_hash, chapters, total, paths, translated
        )
        assert success
        
        checkpoint_path = self.manager._get_checkpoint_path(self.test_hash)
        assert checkpoint_path.exists()

    def test_load_checkpoint(self):
        """Should load saved checkpoint."""
        chapters = [0, 1]
        total = 5
        paths = ["ch1.html", "ch2.html"]
        translated = {0: "<p>T1</p>", 1: "<p>T2</p>"}

        self.manager.save_checkpoint(self.test_hash, chapters, total, paths, translated)
        
        loaded = self.manager.load_checkpoint(self.test_hash)
        assert loaded is not None
        assert loaded["completed_chapters"] == chapters
        assert loaded["total_chapters"] == total

    def test_load_missing_checkpoint(self):
        """Should return None for missing checkpoint."""
        loaded = self.manager.load_checkpoint("nonexistent_hash")
        assert loaded is None

    def test_cleanup_checkpoint(self):
        """Should delete checkpoint file."""
        chapters = [0]
        self.manager.save_checkpoint(self.test_hash, chapters, 1, ["ch1.html"], {})
        
        checkpoint_path = self.manager._get_checkpoint_path(self.test_hash)
        assert checkpoint_path.exists()
        
        success = self.manager.cleanup_checkpoint(self.test_hash)
        assert success
        assert not checkpoint_path.exists()

    def test_mark_checkpoint_complete(self):
        """Should mark checkpoint as complete."""
        chapters = [0, 1, 2]
        self.manager.save_checkpoint(self.test_hash, chapters, 3, ["ch1", "ch2", "ch3"], {})
        
        success = self.manager.mark_checkpoint_complete(self.test_hash)
        assert success
        
        checkpoint_path = self.manager._get_checkpoint_path(self.test_hash)
        with open(checkpoint_path) as f:
            data = json.load(f)
        assert data["status"] == "complete"

    def test_checkpoint_with_language_code(self):
        """Should save and load checkpoint with language code."""
        chapters = [0, 1, 2]
        total = 10
        paths = ["ch1.html", "ch2.html", "ch3.html"]
        translated = {0: "<p>Translated 1</p>", 1: "<p>Translated 2</p>"}
        language_code = "es"

        success = self.manager.save_checkpoint(
            self.test_hash, chapters, total, paths, translated, language_code
        )
        assert success
        
        # File should include language code in name
        checkpoint_path = self.manager._get_checkpoint_path(self.test_hash, language_code)
        assert checkpoint_path.exists()
        assert "es" in checkpoint_path.name

    def test_checkpoint_separate_by_language(self):
        """Checkpoints for different languages should be separate."""
        chapters = [0, 1]
        paths = ["ch1.html"]
        translated = {0: "<p>T1</p>"}

        # Save French checkpoint
        self.manager.save_checkpoint(
            self.test_hash, chapters, 1, paths, translated, "fr"
        )
        
        # Save Spanish checkpoint for same file
        self.manager.save_checkpoint(
            self.test_hash, [0], 1, paths, translated, "es"
        )
        
        # Both should exist as separate files
        fr_path = self.manager._get_checkpoint_path(self.test_hash, "fr")
        es_path = self.manager._get_checkpoint_path(self.test_hash, "es")
        
        assert fr_path.exists()
        assert es_path.exists()
        assert fr_path != es_path

    def test_backwards_compatibility_missing_language_code(self):
        """Should handle checkpoints without language_code field."""
        # Create a checkpoint without language_code (old format)
        checkpoint = {
            "file_hash": self.test_hash,
            "completed_chapters": [0],
            "total_chapters": 1,
            "chapter_paths": ["ch1.html"],
            "translated_chapters": {},
            "status": "in_progress",
        }
        
        checkpoint_path = self.manager._get_checkpoint_path(self.test_hash, "fr")
        checkpoint_path.parent.mkdir(parents=True, exist_ok=True)
        
        import json
        with open(checkpoint_path, "w") as f:
            json.dump(checkpoint, f)
        
        # Should load and add default language_code
        loaded = self.manager.load_checkpoint(self.test_hash, "fr")
        assert loaded is not None
        assert loaded.get("language_code", "fr") == "fr"
