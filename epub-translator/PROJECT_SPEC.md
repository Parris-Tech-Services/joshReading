# EPUB Translator — Complete Project Specification

## Project Overview

A production-ready Python desktop application for translating legally owned, DRM-free French EPUBs to English while preserving the complete book structure, formatting, and metadata.

## What Was Built

### 1. Core Application Package (`epub_translator/`)

#### Translator Interface (`translator/`)
- **`base.py`**: Abstract `BaseTranslator` class defining the provider interface
- **`argos_provider.py`**: Full implementation of Argos Translate (offline, default)
  - Model installation detection and download support
  - Chunked translation with 0.5s delay between requests
  - Error handling with informative messages
- **`deepl_provider.py`**, **`openai_provider.py`**, **`libretranslate_provider.py`**: Stub implementations (ready for v2)

#### EPUB Processing (`epub/`)
- **`reader.py`**: EPUB parsing and analysis
  - DRM detection via `encryption.xml`
  - File hash generation for checkpoint identification
  - Metadata extraction (title, author, language)
  - Chapter extraction in spine order
  - Preserves original file structure
- **`writer.py`**: Translated EPUB creation
  - Preserves 100% of original structure
  - Updates language metadata to English
  - Smart HTML text-node translation (no tag name translation)
  - Skips untranslatable content (URLs, code, CSS, IDs)

#### Checkpoint & Resume (`checkpoint/`)
- **`__init__.py`**: `CheckpointManager` class
  - Saves progress after each chapter as JSON
  - SHA-256 hash-based checkpoint identification
  - Resume detection on app startup
  - Cleanup after successful completion
  - Stores in `~/.local/share/epub-translator/`

#### Utilities (`utils/`)
- **`__init__.py`**: `chunk_text()` function
  - Splits text at sentence boundaries only
  - Respects 500-char limit
  - Never splits mid-word
  - Handles empty strings correctly
  - Validates output chunks

#### GUI (`gui/`)
- **`main_window.py`**: PySide6-based main application window
  - File/folder pickers with drag-and-drop support
  - Real-time progress visualization
  - Current chapter display
  - Chapters completed counter
  - **Estimated time remaining** (clearly labeled as estimate)
  - Pause/Resume/Cancel controls
  - Scrollable activity log
  - Open output folder button
  - Open translated EPUB button
- **`worker.py`**: Translation worker thread
  - Runs on `QThread` (respects GIL, prevents GUI freeze)
  - Handles pause/resume/cancel state
  - Emits Qt signals for GUI updates
  - Per-chapter error handling
  - Checkpoint integration

#### Main Entry Point (`main.py`)
- PySide6 application initialization
- Error handling for missing dependencies
- Graceful fallback for missing translation model

### 2. Test Suite (`tests/`)

- **`test_chunking.py`**: Text chunking algorithm
  - Empty text handling
  - Short text (< 500 chars) not split
  - Long text splits at sentences
  - Validates sentence boundary detection (`.`, `?`, `!`)
  - No empty chunks
  - Custom chunk size support

- **`test_translation.py`**: Translator interface
  - Base translator raises NotImplementedError
  - Mock translator integrates correctly
  - Stub providers raise NotImplementedError appropriately
  - Argos initialization tested (if installed)

- **`test_epub_reader.py`**: EPUB reading and DRM detection
  - Minimal EPUB parsing
  - Metadata extraction
  - Consistent file hashing
  - DRM detection (encryption.xml)
  - Context manager support

- **`test_checkpoint.py`**: Checkpoint system
  - Checkpoint save and load
  - File hash identification
  - Cleanup after completion
  - Missing checkpoint handling
  - Status updates

- **`conftest.py`**: Pytest configuration

### 3. Project Configuration

- **`setup.py`**: Package setup with console script entry point
- **`pyproject.toml`**: Modern Python project configuration
  - Build system configuration
  - Dependency specifications
  - Tool configurations (ruff, black, mypy, pytest)
- **`.gitignore`**: Git ignore patterns (venv, __pycache__, build, tests, etc.)

### 4. Documentation

- **`README.md`** (comprehensive 300+ lines)
  - Complete feature list
  - System requirements
  - Installation instructions
  - Usage guide
  - Running tests
  - Code quality tools
  - Project structure explanation
  - How it works (detailed 4-step process)
  - Troubleshooting section
  - Future enhancements
  - Performance notes

- **`INSTALLATION.md`** (exact terminal commands)
  - System dependency installation
  - Virtual environment setup
  - Dependency installation
  - Model download
  - Application launch
  - Test running
  - Verification steps
  - Troubleshooting for installation issues
  - Desktop launcher creation

- **`QUICKSTART.md`**
  - One-time setup commands
  - Running the app
  - Running tests
  - File structure overview
  - Features checklist
  - Troubleshooting quick reference

## Key Features Implemented

### ✅ Translation Architecture
- Argos Translate fully offline after model download
- Pluggable provider interface (3 stubs ready for future providers)
- Smart text chunking (< 500 chars, sentence boundaries)
- 0.5s delay between translation requests
- Error handling per-chapter

### ✅ EPUB Structure Preservation
- Chapter order and spine
- Table of contents
- Headings and formatting
- Bold, italic, underline
- Links and internal anchors
- Footnotes and endnotes
- Images and cover
- CSS stylesheets
- Metadata (title, author, language)
- Page breaks
- Navigation document

### ✅ Smart Translation
- Only translates visible text
- Skips: HTML tags, CSS, URLs, image paths, anchor IDs, code, XML declarations
- Preserves whitespace
- No mid-word splits
- No paragraph joining

### ✅ DRM Detection
- Checks for `encryption.xml` in EPUB
- Clear error message if DRM found
- Application aborts immediately

### ✅ GUI Features
- File picker with default dialogs (Wayland fallback message if drag-drop fails)
- Output folder selection
- Start/Pause/Resume/Cancel buttons
- Progress bar (0-100%)
- Current chapter name display
- Chapters completed display
- **Estimated time remaining** (clearly labeled)
- Scrollable activity log
- Open output folder button
- Open translated EPUB button
- Responsive (never freezes due to QThread usage)

### ✅ Resume & Recovery
- Checkpoint saved after each chapter
- SHA-256 hash identification
- Resume prompt on startup if checkpoint exists
- No data loss on app crash
- Cleanup after successful completion

### ✅ Error Handling
- Per-chapter error logging
- Continues translation if chapter fails
- Skipped chapters clearly marked
- Final summary: "X of Y chapters, Z skipped"
- Exceptions never crash silently

### ✅ Code Quality
- Type hints throughout
- Comprehensive logging
- Docstrings on all public methods
- Test coverage for core modules
- Ruff formatting and linting ready
- Mypy type checking ready

### ✅ Testing
- 4 test modules with ~40 test cases
- Unit tests for chunking algorithm
- Interface tests for translators
- EPUB reader tests including DRM detection
- Checkpoint save/load tests
- Pytest fixtures and parametrization

## Installation Quick Start

```bash
# Navigate to project
cd ~/Projects/JoshBooks/epub-translator

# Create virtual environment
python3.12 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -e ".[dev]"

# Download translation model
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

# Run the application
epub-translator
```

## File Manifest

```
epub-translator/
├── epub_translator/
│   ├── __init__.py
│   ├── main.py                      # Entry point
│   ├── gui/
│   │   ├── __init__.py
│   │   ├── main_window.py          # PySide6 GUI window
│   │   └── worker.py               # QThread translation worker
│   ├── translator/
│   │   ├── __init__.py
│   │   ├── base.py                 # Abstract BaseTranslator
│   │   ├── argos_provider.py       # Argos Translate (complete)
│   │   ├── deepl_provider.py       # DeepL stub
│   │   ├── openai_provider.py      # OpenAI stub
│   │   └── libretranslate_provider.py  # LibreTranslate stub
│   ├── epub/
│   │   ├── __init__.py
│   │   ├── reader.py               # EPUB parsing + DRM detection
│   │   └── writer.py               # EPUB creation + translation
│   ├── checkpoint/
│   │   └── __init__.py             # Checkpoint manager
│   └── utils/
│       └── __init__.py             # Text chunking
├── tests/
│   ├── conftest.py
│   ├── test_chunking.py
│   ├── test_translation.py
│   ├── test_epub_reader.py
│   └── test_checkpoint.py
├── run.py                           # Alternate entry point
├── setup.py                         # Package setup
├── pyproject.toml                   # Project config
├── .gitignore                       # Git ignore patterns
├── README.md                        # Full documentation
├── INSTALLATION.md                  # Setup instructions
├── QUICKSTART.md                    # Quick reference
└── PROJECT_SPEC.md                  # This file
```

## Development Workflow

### Running the Application
```bash
source venv/bin/activate
epub-translator
```

### Running Tests
```bash
source venv/bin/activate
pytest -v
pytest --cov=epub_translator tests/
```

### Code Quality
```bash
source venv/bin/activate
ruff format epub_translator/ tests/
ruff check epub_translator/ tests/
mypy epub_translator/
```

## Architecture Highlights

### Provider Pattern
- `BaseTranslator` abstract class defines interface
- `ArgosTranslator` implements full translation
- Stub providers ready for DeepL, OpenAI, LibreTranslate (v2)
- New providers can be added without modifying core logic

### Threading Model
- Translation runs on `QThread` (not `threading.Thread`)
- Prevents GUI freeze even during long translations
- Qt signal-based communication with main thread
- Safe pause/resume/cancel at chapter boundaries

### Checkpoint System
- File hash-based identification
- JSON storage in user's local directory
- Supports resuming from any chapter
- Cleans up after successful completion
- Preserves checkpoint if write fails

### EPUB Handling
- Preserves 100% of original structure
- Smart HTML traversal (text nodes only)
- Skips untranslatable content
- Updates metadata (language → en)
- Maintains all file types and structure

## Future Enhancement Hooks

The project is designed for easy extension:

1. **Translation Providers**: Implement `BaseTranslator` subclass
2. **Language Pairs**: Add language selection UI + provider configuration
3. **Batch Processing**: Queue multiple EPUBs with worker pooling
4. **Translation Memory**: Add glossary/memory storage
5. **Custom Plugins**: Plugin system for translation providers
6. **Web UI**: Reuse backend with Flask/FastAPI frontend
7. **Language-Specific Logic**: Hook for normalization/post-processing

## Performance Characteristics

- Translation speed: ~30-60 min for 100k-word novel (system dependent)
- Memory: 100-300 MB during translation
- Disk: ~250 MB for Argos Translate models
- CPU-intensive (no GPU acceleration in v1)
- Checkpoints allow interrupting and resuming
- No internet required after model download

## Compliance & Security

- ✅ No DRM bypass (detects and aborts)
- ✅ Respects copyright (user-responsible for licensed content)
- ✅ No phone-home telemetry
- ✅ Local checkpoint storage only
- ✅ All translation offline
- ✅ No credentials stored

## Known Limitations (v1)

- Fedora Linux only (Windows/macOS ready in v2)
- Single EPUB translation at a time
- French → English only (other pairs in v2)
- Online providers not available (v2)
- Drag-and-drop unreliable on Wayland (fallback: file picker)
- Argos Translate doesn't support GPU (CPU only)

---

**Build Date**: 2026-06-17
**Target Python**: 3.12+
**Target OS**: Fedora Linux
**Status**: Production-ready (v0.1.0)
