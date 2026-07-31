"""Translation worker thread for non-blocking EPUB translation."""

import logging
import time
from typing import Optional

from PySide6.QtCore import QThread, Signal

from epub_translator.checkpoint import CheckpointManager
from epub_translator.epub import EPUBReader, EPUBWriter
from epub_translator.translator.argos_provider import ArgosTranslator, LANGUAGE_NAMES
from epub_translator.utils import chunk_text

logger = logging.getLogger(__name__)

DELAY_BETWEEN_REQUESTS = 0.5  # seconds


class TranslationWorker(QThread):
    """Worker thread for EPUB translation."""

    # Signals
    progress_updated = Signal(int, str, int, int, float)  # percentage, chapter_name, completed, total, eta_seconds
    chapter_completed = Signal(str, int)  # chapter_name, chapter_index
    translation_finished = Signal(bool, str)  # success, message
    error_occurred = Signal(str)  # error message
    status_changed = Signal(str)  # status message

    def __init__(
        self,
        input_path: str,
        output_path: str,
        translator: ArgosTranslator,
        source_language: str = "fr",
    ):
        """
        Initialize translation worker.

        Args:
            input_path: Path to input EPUB
            output_path: Path to output EPUB
            translator: ArgosTranslator instance
            source_language: Source language code
        """
        super().__init__()
        self.input_path = input_path
        self.output_path = output_path
        self.translator = translator
        self.source_language = source_language
        self.checkpoint_manager = CheckpointManager()
        
        self._paused = False
        self._cancel_requested = False
        self.start_time = None
        self.chapters_completed = 0
        self.total_chapters = 0

    def pause(self) -> None:
        """Pause translation."""
        self._paused = True
        self.status_changed.emit("Paused")

    def resume(self) -> None:
        """Resume translation."""
        self._paused = False
        self.status_changed.emit("Translating...")

    def cancel(self) -> None:
        """Cancel translation."""
        self._cancel_requested = True
        self.status_changed.emit("Cancelling...")

    def run(self) -> None:
        """Execute translation in background thread."""
        try:
            self._execute_translation()
        except Exception as e:
            logger.error(f"Translation worker error: {e}")
            self.error_occurred.emit(str(e))
            self.translation_finished.emit(False, f"Translation failed: {e}")

    def _execute_translation(self) -> None:
        """Main translation logic."""
        self.start_time = time.time()
        lang_name = LANGUAGE_NAMES.get(self.source_language, self.source_language)

        try:
            # Read original EPUB
            self.status_changed.emit("Reading EPUB...")
            with EPUBReader(self.input_path) as reader:
                file_hash = reader.get_file_hash()
                chapters = reader.get_chapters()
                metadata = reader.get_metadata()
                all_files = reader.get_all_files()

            self.total_chapters = len(chapters)

            # Log source language
            self.status_changed.emit(f"Translating from {lang_name} to English")

            # Check for resume
            checkpoint = self.checkpoint_manager.load_checkpoint(file_hash, self.source_language)
            completed_chapters = []
            translated_chapters = {}

            if checkpoint and checkpoint["status"] == "in_progress":
                response = self._ask_resume(checkpoint)
                if response:
                    completed_chapters = checkpoint["completed_chapters"]
                    translated_chapters = {
                        int(k): v for k, v in checkpoint["translated_chapters"].items()
                    }
                    self.chapters_completed = len(completed_chapters)
                    self.status_changed.emit(f"Resuming from chapter {self.chapters_completed + 1}...")

            # Translate chapters
            skipped_chapters = []
            # Determine if CJK language for smart chunking
            is_cjk = self.translator.is_cjk_language(self.source_language)

            for idx, chapter in enumerate(chapters):
                if self._cancel_requested:
                    self.status_changed.emit("Translation cancelled")
                    self.translation_finished.emit(False, "Translation cancelled by user")
                    return

                # Wait if paused
                while self._paused:
                    time.sleep(0.1)

                if idx in completed_chapters:
                    continue

                try:
                    self.status_changed.emit(f"Translating: {chapter['title']}")
                    translated_html = self._translate_chapter(chapter["raw_html"], is_cjk)
                    translated_chapters[idx] = translated_html

                    self.chapters_completed += 1
                    completed_chapters.append(idx)

                    # Save checkpoint after each chapter
                    self.checkpoint_manager.save_checkpoint(
                        file_hash,
                        completed_chapters,
                        self.total_chapters,
                        [c["path"] for c in chapters],
                        translated_chapters,
                        self.source_language,
                    )

                    # Update progress
                    self._update_progress(chapter["title"])
                    self.chapter_completed.emit(chapter["title"], idx)

                except Exception as e:
                    logger.error(f"Error translating chapter {idx}: {e}")
                    skipped_chapters.append((idx, chapter["title"], str(e)))
                    self.status_changed.emit(f"Skipped: {chapter['title']} (error)")

            # Write translated EPUB
            if self.chapters_completed == 0:
                self.translation_finished.emit(
                    False, "No chapters were translated"
                )
                return

            self.status_changed.emit("Writing translated EPUB...")
            chapters_for_write = [
                {
                    **ch,
                    "translated_html": translated_chapters.get(idx, ch.get("raw_html")),
                }
                for idx, ch in enumerate(chapters)
            ]

            writer = EPUBWriter(self.output_path)
            writer.create_translated_epub(
                self.input_path,
                chapters_for_write,
                metadata_updates={"language": "en"},
            )

            # Mark complete and clean up checkpoint
            self.checkpoint_manager.mark_checkpoint_complete(file_hash, self.source_language)
            self.checkpoint_manager.cleanup_checkpoint(file_hash, self.source_language)

            # Report results
            success = self.chapters_completed == self.total_chapters
            if skipped_chapters:
                message = (
                    f"Translation complete. {self.chapters_completed}/{self.total_chapters} "
                    f"chapters translated. {len(skipped_chapters)} chapters skipped."
                )
            else:
                message = f"Translation complete! All {self.total_chapters} chapters translated."

            self.translation_finished.emit(success, message)

        except Exception as e:
            logger.error(f"Translation execution error: {e}")
            raise

    def _translate_chapter(self, html_content: str, is_cjk: bool = False) -> str:
        """
        Translate chapter HTML content.

        Args:
            html_content: HTML content to translate
            is_cjk: Whether to use CJK chunking

        Returns:
            Translated HTML
        """
        from bs4 import BeautifulSoup, NavigableString

        soup = BeautifulSoup(html_content, "html.parser")
        skip_tags = {"script", "style", "code", "pre", "math", "svg"}

        def translate_recursive(element):
            """Recursively translate text nodes."""
            if isinstance(element, NavigableString):
                if element.parent and element.parent.name in skip_tags:
                    return

                text = str(element).strip()
                if text:
                    try:
                        chunks = chunk_text(text, max_chunk_size=500, is_cjk=is_cjk)
                        translations = []
                        for chunk in chunks:
                            translated = self.translator.translate(chunk)
                            translations.append(translated)
                            time.sleep(DELAY_BETWEEN_REQUESTS)

                        translated_text = " ".join(translations)
                        element.replace_with(translated_text)
                    except Exception as e:
                        logger.warning(f"Failed to translate: {text[:50]}... - {e}")
            else:
                if element.name not in skip_tags:
                    for child in list(element.children):
                        translate_recursive(child)

        translate_recursive(soup)
        return str(soup)

    def _update_progress(self, chapter_name: str) -> None:
        """Update progress signal."""
        if self.total_chapters == 0:
            return

        percentage = int((self.chapters_completed / self.total_chapters) * 100)
        elapsed = time.time() - self.start_time
        rate = self.chapters_completed / elapsed if elapsed > 0 else 0
        remaining = (self.total_chapters - self.chapters_completed) / rate if rate > 0 else 0

        self.progress_updated.emit(
            percentage,
            chapter_name,
            self.chapters_completed,
            self.total_chapters,
            remaining,
        )

    def _ask_resume(self, checkpoint: dict) -> bool:
        """Ask user if they want to resume from checkpoint."""
        # This will be connected to a dialog in the GUI
        # For now, always resume if checkpoint exists
        return True
