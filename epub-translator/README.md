# EPUB Translator — French to English

A polished, reliable desktop application for translating legally owned, DRM-free French EPUBs to English while preserving the book's complete structure and formatting.

## Features

- **Offline Translation**: Uses Argos Translate for fully offline French-to-English translation
- **Structure Preservation**: Maintains chapters, table of contents, headings, formatting, images, links, footnotes, CSS, and metadata
- **Smart Translation**:
  - Chunks text intelligently to respect engine limits
  - Splits only at sentence boundaries, never mid-word
  - Skips HTML tags, code, URLs, and other non-translatable content
- **Resume & Recovery**: Saves progress after each chapter; resume translation if interrupted
- **DRM Detection**: Detects and rejects DRM-protected files immediately with a clear message
- **Comprehensive Progress Tracking**:
  - Current chapter name
  - Chapters completed count
  - Overall progress percentage
  - Estimated time remaining (clearly labeled as estimate)
- **Pause/Resume/Cancel**: Full control over translation process with checkpoint recovery
- **Responsive GUI**: All translation work runs on background threads; GUI never freezes
- **Cross-Provider Design**: Pluggable translator interface ready for DeepL, OpenAI, LibreTranslate in future versions

## Requirements

- **OS**: Fedora Linux (or other Linux distributions with similar package management)
- **Python**: 3.12 or later
- **Memory**: 2+ GB available RAM recommended
- **Disk**: ~200 MB for Argos Translate models

## Installation

### Step 1: System Dependencies

Install required system packages on Fedora:

```bash
sudo dnf install python3.12 python3.12-devel python3-pip git libxcb-cursor0 libxcb-xfixes0
```

Or using `dnf groupinstall`:

```bash
sudo dnf groupinstall "C Development Tools and Libraries"
```

### Step 2: Create Virtual Environment

Create and activate a Python virtual environment:

```bash
# Clone or navigate to the project
cd ~/Projects/JoshBooks/epub-translator

# Create virtual environment
python3.12 -m venv venv

# Activate it
source venv/bin/activate

# Upgrade pip, setuptools, wheel
pip install --upgrade pip setuptools wheel
```

### Step 3: Install Dependencies

Install the application and all dependencies:

```bash
# Install in development mode (recommended)
pip install -e ".[dev]"

# OR for production only:
# pip install -e .
```

This installs:
- PySide6 (GUI framework)
- ebooklib (EPUB handling)
- BeautifulSoup4 (HTML parsing)
- lxml (XML processing)
- argostranslate (offline translation engine)
- pytest, ruff (development tools)

### Step 4: Download Translation Model

Download the French-to-English model for Argos Translate:

```bash
# Activate venv first if not already active
source venv/bin/activate

# Download the model (~150 MB)
python -c "
import argostranslate.package
argostranslate.package.update_package_index()
packages = argostranslate.package.get_available_packages()
for package in packages:
    if package.from_code == 'fr' and package.to_code == 'en':
        argostranslate.package.install_package(package)
        break
print('French-to-English model installed successfully!')
"
```

**Note**: The app also offers to download the model on first run if it detects it's missing.

## Running the Application

Ensure your virtual environment is activated:

```bash
source venv/bin/activate
```

Then run the application:

```bash
# Using console script (after installation)
epub-translator

# OR directly with Python
python -m epub_translator.main

# OR from the project directory
python epub_translator/main.py
```

The GUI window will open. You can now:

1. **Select Input EPUB**: Click "Browse..." or drag a French EPUB file
2. **Select Output Folder**: Choose where the translated EPUB will be saved
3. **Start Translation**: Click "Start Translation"
4. **Monitor Progress**: Watch the progress bar, current chapter, and estimated time remaining
5. **Control**: Pause, resume, or cancel at any time
6. **Access Results**: Open the output folder or open the translated EPUB directly

## Running Tests

With the virtual environment activated:

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=epub_translator tests/

# Run specific test file
pytest tests/test_chunking.py -v

# Run tests matching a pattern
pytest tests/ -k "epub" -v
```

Test files cover:
- `test_chunking.py` — Text chunking at sentence boundaries
- `test_translation.py` — Translator interface and providers
- `test_epub_reader.py` — EPUB parsing and DRM detection
- `test_checkpoint.py` — Resume checkpoint save/load

## Code Quality

### Linting and Formatting

```bash
# Format code with ruff
ruff format epub_translator/ tests/

# Check for lint errors
ruff check epub_translator/ tests/

# Type checking with mypy
mypy epub_translator/
```

## Project Structure

```
epub_translator/
├── main.py                 # Application entry point
├── __init__.py
├── gui/
│   ├── main_window.py      # Main GUI window (PySide6)
│   ├── worker.py           # Translation worker thread
│   └── __init__.py
├── translator/
│   ├── base.py             # BaseTranslator abstract interface
│   ├── argos_provider.py   # Argos Translate implementation
│   ├── deepl_provider.py   # DeepL stub (v2+)
│   ├── openai_provider.py  # OpenAI stub (v2+)
│   ├── libretranslate_provider.py  # LibreTranslate stub (v2+)
│   └── __init__.py
├── epub/
│   ├── reader.py           # EPUB parsing and DRM detection
│   ├── writer.py           # EPUB creation with translated content
│   └── __init__.py
├── checkpoint/
│   └── __init__.py         # Resume/recovery checkpoint system
├── utils/
│   └── __init__.py         # Text chunking utilities
└── __init__.py
tests/
├── conftest.py             # Pytest configuration
├── test_chunking.py        # Text chunking tests
├── test_translation.py     # Translator tests
├── test_epub_reader.py     # EPUB reader tests
└── test_checkpoint.py      # Checkpoint tests
```

## How It Works

### 1. EPUB Reading
- Opens the EPUB as a ZIP container
- Detects DRM by checking for `encryption.xml`
- Extracts chapters in spine order from the OPF package
- Preserves all structural metadata

### 2. Translation Pipeline
- Reads each chapter's HTML
- Walks through text nodes individually (preserves parent tags)
- Skips non-translatable content: tags, URLs, code, CSS, IDs
- Chunks text at sentence boundaries (< 500 chars per chunk)
- Translates via Argos Translate (offline, no internet required)
- Adds 0.5s delay between requests to avoid overloading the engine

### 3. Progress & Resume
- After each chapter, saves checkpoint (SHA-256 hash based)
- Stores completed chapter list and translations
- On restart, detects checkpoint and offers to resume
- After successful completion, cleans up checkpoint

### 4. EPUB Writing
- Creates new EPUB with original structure
- Replaces text with translations
- Updates language metadata to English (`en`)
- Preserves all original files, CSS, images, navigation

### 5. GUI Thread Model
- Runs all translation work in `QThread` (not `threading.Thread`)
- Communicates with GUI via Qt signals
- GUI remains responsive during translation
- Gracefully handles pause/resume/cancel

## Troubleshooting

### "ImportError: No module named 'PySide6'"
Ensure the virtual environment is activated and dependencies installed:
```bash
source venv/bin/activate
pip install -e ".[dev]"
```

### "Translation model not installed"
The app will offer to download it on first run. Alternatively:
```bash
python -c "import argostranslate.package; argostranslate.package.update_package_index(); packages = argostranslate.package.get_available_packages(); [argostranslate.package.install_package(p) for p in packages if p.from_code == 'fr' and p.to_code == 'en']"
```

### "Drag and drop not supported on this platform"
On Wayland, drag-and-drop may not work reliably. Use the file picker dialog instead.

### Application crashes or freezes
- Ensure you're using Python 3.12+
- Check available system memory (minimum 2 GB recommended)
- Look for error details in the activity log or terminal output
- Try resuming from the checkpoint if translation was interrupted

### EPUB doesn't open in reader after translation
- Verify the input was a valid EPUB
- Check the output file exists and is readable
- Try opening with a different EPUB reader (Calibre, Foliate, etc.)

## Future Enhancements (v2+)

- DeepL provider for higher-quality translation
- OpenAI GPT provider for context-aware translation
- LibreTranslate provider for self-hosted option
- Windows and macOS support
- Batch translation of multiple EPUBs
- Custom translation provider plugins
- Language pair selection (not just French→English)
- Translation memory / term glossary support
- Web UI alongside desktop app

## Performance Notes

- Translation speed depends on book length and system performance
- Typical fiction book (100k words): 30–60 minutes on modern systems
- Argos Translate uses CPU; GPU acceleration not yet supported
- Checkpoints allow interrupting large books and resuming later
- No internet required after model download

## License

MIT License

## Support

For issues or questions:
- Check the [Troubleshooting](#troubleshooting) section above
- Review test files for usage examples
- Check application logs in `~/.local/share/epub-translator/` for checkpoint data

---

**Note**: This application respects copyright and DRM laws. It only works with legally owned, DRM-free EPUB files. Always ensure you have the right to translate and distribute any translated content.
