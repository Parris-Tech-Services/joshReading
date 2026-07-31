# EPUB Translator — Installation & Quick Start Guide

This file contains the exact terminal commands to set up and run the EPUB Translator application on Fedora Linux.

## Prerequisites

- Fedora Linux (tested on Fedora 40+)
- Internet connection (for downloading Argos Translate model)
- ~200 MB free disk space (for translation model)
- ~2 GB free RAM

## Complete Installation Steps

### 1. Install System Dependencies

```bash
# Update package manager
sudo dnf update -y

# Install development tools and Python
sudo dnf install -y python3.12 python3.12-devel python3.12-pip \
    git libxcb-cursor0 libxcb-xfixes0 gcc g++ make

# Or install full development environment
sudo dnf groupinstall -y "C Development Tools and Libraries"
```

### 2. Clone or Navigate to Project

```bash
# Navigate to the epub-translator directory
cd ~/Projects/JoshBooks/epub-translator

# Verify structure
ls -la
# Should show: epub_translator/ tests/ setup.py pyproject.toml README.md etc.
```

### 3. Create Python Virtual Environment

```bash
# Create virtual environment
python3.12 -m venv venv

# Activate it
source venv/bin/activate

# You should see (venv) at the start of your prompt
# Verify you're using the correct Python
python --version  # Should show Python 3.12.x
which python      # Should show path inside venv/
```

### 4. Upgrade pip and Install Dependencies

```bash
# Upgrade pip, setuptools, wheel
pip install --upgrade pip setuptools wheel

# Install the project with all dependencies
pip install -e ".[dev]"

# This installs:
# - PySide6 (GUI framework)
# - ebooklib (EPUB parsing)
# - BeautifulSoup4 (HTML processing)
# - argostranslate (offline translation)
# - pytest, ruff (dev tools)

# Verify installation
pip list | grep -E "PySide|ebooklib|BeautifulSoup|argostranslate"
```

### 5. Download French-to-English Translation Model

```bash
# Make sure venv is activated
source venv/bin/activate

# Download the model (~150 MB)
python << 'EOF'
import argostranslate.package

print("Updating package index...")
argostranslate.package.update_package_index()

print("Finding French-to-English package...")
packages = argostranslate.package.get_available_packages()
for package in packages:
    if package.from_code == 'fr' and package.to_code == 'en':
        print(f"Installing {package}...")
        argostranslate.package.install_package(package)
        print("✓ French-to-English model installed successfully!")
        break
else:
    print("⚠ French-to-English package not found")
EOF
```

## Running the Application

### Start the GUI Application

```bash
# Activate virtual environment (if not already active)
source venv/bin/activate

# Run the application
epub-translator

# Alternative methods:
python -m epub_translator.main
python epub_translator/main.py
```

The GUI window will appear. You can now:
1. Click "Browse..." to select a French EPUB file
2. Click "Browse..." to select an output folder
3. Click "Start Translation"
4. Monitor progress, pause/resume as needed

### Command Line Testing

```bash
# Activate venv
source venv/bin/activate

# Test the chunking algorithm
python -c "
from epub_translator.utils import chunk_text
text = 'This is test. ' * 50
chunks = chunk_text(text)
print(f'Text length: {len(text)}')
print(f'Number of chunks: {len(chunks)}')
print(f'First chunk: {chunks[0][:80]}...')
"

# Test EPUB reading (requires a test EPUB)
python -c "
from epub_translator.epub.reader import EPUBReader
# Replace 'test.epub' with actual file
# reader = EPUBReader('test.epub')
# print(reader.get_metadata())
print('EPUB reader module loaded successfully')
"
```

## Running Tests

```bash
# Activate venv
source venv/bin/activate

# Run all tests
pytest -v

# Run specific test file
pytest tests/test_chunking.py -v

# Run tests with coverage report
pytest --cov=epub_translator tests/ -v

# Run only checkpoint tests
pytest tests/test_checkpoint.py -v

# Expected output should show all tests passing
```

## Code Quality Checks

```bash
# Activate venv
source venv/bin/activate

# Format code with ruff
ruff format epub_translator/ tests/

# Check for linting issues
ruff check epub_translator/ tests/

# Type check with mypy
mypy epub_translator/
```

## Verify Installation

```bash
# Create a quick verification script
source venv/bin/activate

python << 'EOF'
print("✓ Checking installation...")

try:
    from PySide6.QtWidgets import QApplication
    print("✓ PySide6 installed")
except ImportError as e:
    print(f"✗ PySide6 error: {e}")

try:
    import ebooklib
    print("✓ ebooklib installed")
except ImportError as e:
    print(f"✗ ebooklib error: {e}")

try:
    from bs4 import BeautifulSoup
    print("✓ BeautifulSoup4 installed")
except ImportError as e:
    print(f"✗ BeautifulSoup4 error: {e}")

try:
    import argostranslate.translate
    import argostranslate.package
    installed = argostranslate.package.get_installed_packages()
    has_fr_en = any(p.from_code == 'fr' and p.to_code == 'en' for p in installed)
    if has_fr_en:
        print("✓ Argos Translate with French-to-English model installed")
    else:
        print("⚠ Argos Translate installed but model not found (run model download step)")
except ImportError as e:
    print(f"✗ Argos Translate error: {e}")

print("\nAll systems ready! Run 'epub-translator' to start.")
EOF
```

## Troubleshooting Installation

### Python version mismatch
```bash
# Check Python version
python --version

# If not 3.12, create venv explicitly
python3.12 -m venv venv
source venv/bin/activate
```

### pip install fails with permission error
```bash
# Update pip first
pip install --upgrade pip setuptools wheel

# Install with --user flag if needed
pip install --user -e ".[dev]"
```

### PySide6 installation fails
```bash
# Try installing build dependencies first
sudo dnf install -y qt6-qtbase-devel qt6-qtdeclarative-devel

# Then retry pip install
pip install PySide6==6.6.0
```

### Argos model download fails
```bash
# Check internet connection
ping 8.8.8.8

# Try manual download with more verbosity
python -c "
import logging
logging.basicConfig(level=logging.DEBUG)
import argostranslate.package
argostranslate.package.update_package_index()
"
```

### Cannot find epub-translator command
```bash
# Ensure you're in the project directory
cd ~/Projects/JoshBooks/epub-translator

# Ensure venv is activated
source venv/bin/activate

# Try running directly
python -m epub_translator.main

# If that works, reinstall in editable mode
pip install -e .
```

## Next Steps

1. **Translate your first book**: Run `epub-translator` and select a French EPUB
2. **Run the test suite**: Execute `pytest -v` to verify all components
3. **Check the README.md**: Full documentation and features
4. **Review code structure**: Explore the `epub_translator/` package to understand architecture

## Creating a Desktop Launcher (Optional)

Create `~/.local/share/applications/epub-translator.desktop`:

```bash
mkdir -p ~/.local/share/applications

cat > ~/.local/share/applications/epub-translator.desktop << 'EOF'
[Desktop Entry]
Type=Application
Name=EPUB Translator
Comment=Translate French EPUBs to English
Exec=bash -c 'cd ~/Projects/JoshBooks/epub-translator && source venv/bin/activate && epub-translator'
Icon=document
Terminal=false
Categories=Office;WordProcessor;
EOF

# Update desktop database
update-desktop-database ~/.local/share/applications
```

Now you can launch the app from your application menu!

---

## Quick Reference

```bash
# Activate environment
source ~/Projects/JoshBooks/epub-translator/venv/bin/activate

# Run application
epub-translator

# Run tests
cd ~/Projects/JoshBooks/epub-translator && pytest -v

# Deactivate environment when done
deactivate
```

For detailed documentation, see README.md.
