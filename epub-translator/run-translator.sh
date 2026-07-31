#!/bin/bash
# EPUB Translator Launcher

cd "$(dirname "$0")"
source venv/bin/activate
python -m epub_translator.main
