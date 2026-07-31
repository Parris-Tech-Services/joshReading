# Quick Start

## Installation (One-Time Setup)

```bash
cd ~/Projects/JoshBooks/epub-translator

# Create and activate virtual environment
python3.12 -m venv venv
source venv/bin/activate

# Install dependencies
pip install --upgrade pip setuptools wheel
pip install -e ".[dev]"

# Download translation model (~150 MB)
python -c "
import argostranslate.package
argostranslate.package.update_package_index()
packages = argostranslate.package.get_available_packages()
for p in packages:
    if p.from_code == 'fr' and p.to_code == 'en':
        argostranslate.package.install_package(p)
        print('✓ Model installed')
        break
"
```

## Running the App

```bash
# Activate environment
source ~/Projects/JoshBooks/epub-translator/venv/bin/activate

# Run the GUI
epub-translator

# Or directly:
python -m epub_translator.main
```

## Running Tests

```bash
# From project directory with venv activated
pytest -v

# With coverage
pytest --cov=epub_translator tests/
```

## File Structure

```
epub-translator/
├── epub_translator/          # Main package
│   ├── main.py              # Entry point
│   ├── gui/                 # PySide6 GUI
│   │   ├── main_window.py
│   │   └── worker.py        # Translation thread
│   ├── translator/          # Provider interface
│   │   ├── base.py
│   │   ├── argos_provider.py
│   │   └── [deepl|openai|libretranslate]_provider.py (stubs)
│   ├── epub/                # EPUB handling
│   │   ├── reader.py        # DRM detection, parsing
│   │   └── writer.py        # Output generation
│   ├── checkpoint/          # Resume system
│   │   └── __init__.py      # Checkpoint manager
│   └── utils/               # Utilities
│       └── __init__.py      # Text chunking
├── tests/                   # Test suite
│   ├── test_chunking.py
│   ├── test_translation.py
│   ├── test_epub_reader.py
│   └── test_checkpoint.py
├── README.md                # Full documentation
├── INSTALLATION.md          # Detailed setup guide
├── setup.py                 # Package setup
└── pyproject.toml          # Project config
```

## Key Features Implemented

✓ **Translation Pipeline**
  - Argos Translate (offline, French→English)
  - Pluggable provider interface (DeepL, OpenAI, LibreTranslate ready as stubs)
  - Smart text chunking (< 500 chars, sentence boundaries)
  - 0.5s delay between requests

✓ **EPUB Handling**
  - DRM detection (aborts if encryption.xml found)
  - Structure preservation (chapters, TOC, metadata, images, CSS)
  - Smart HTML traversal (only translates text nodes)
  - Skips: tags, URLs, code, CSS, IDs

✓ **GUI (PySide6)**
  - File/folder pickers
  - Real-time progress display
  - Chapter name, completion count, ETA
  - Pause/Resume/Cancel controls
  - Activity log
  - Open output folder / EPUB buttons

✓ **Resume & Checkpoints**
  - Saves progress after each chapter
  - SHA-256 hash-based checkpoint files
  - Recovery on app restart
  - Cleanup after successful translation

✓ **Error Handling**
  - DRM detection with clear messaging
  - Per-chapter error logging
  - Graceful skip of failed chapters
  - Summary: "X of Y translated, Z skipped"

✓ **Threading**
  - Translation on QThread (respects GIL)
  - GUI never freezes
  - Qt signal-based communication

✓ **Testing**
  - Chunking tests (boundaries, empty, custom size)
  - Translator interface tests (mocks, NotImplementedError)
  - EPUB reader tests (minimal EPUB, metadata, DRM detection)
  - Checkpoint tests (save, load, cleanup)

## Next Steps / Future Work

- [ ] Implement DeepL provider (v2)
- [ ] Implement OpenAI provider (v2)
- [ ] Implement LibreTranslate provider (v2)
- [ ] Windows/macOS support
- [ ] Batch translation of multiple EPUBs
- [ ] Translation memory / glossary
- [ ] Language pair selection (not just FR→EN)
- [ ] GPU acceleration for Argos Translate
- [ ] Web UI alongside desktop app

## Troubleshooting

**"Module not found"**: Ensure venv is activated and dependencies installed
```bash
source venv/bin/activate
pip install -e ".[dev]"
```

**"Translation model not found"**: Download it manually (see Installation above)

**Drag-and-drop not working**: Normal on Wayland; use file picker instead

**EPUB won't open**: Try different reader (Calibre, Foliate, etc.)

---

See README.md for full documentation and INSTALLATION.md for detailed setup.
