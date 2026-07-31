# EPUB Translator — Multi-Language Expansion

## Overview

The EPUB Translator has been expanded to support multiple source languages beyond French. All changes are **backwards compatible** with existing French→English translations.

## Changes Summary

### 1. Argos Translator Provider (`translator/argos_provider.py`)

**New Features:**
- Language codes and human names mapping (15+ languages)
- CJK language identification (`is_cjk_language()` static method)
- Multi-language support:
  - Constructor now takes `source_language` parameter (default: "fr")
  - `set_source_language()` method to switch languages at runtime
- Language discovery:
  - `get_installed_languages()` — returns list of installed X→EN packages
  - `get_available_packages()` — returns all available packages with size/install status
- All methods updated to work with any language, not just French
- Improved error messages that reference actual language names

**Backwards Compatibility:**
- Default source language is "fr" (French)
- All existing code using French-only still works without changes

### 2. Checkpoint System (`checkpoint/__init__.py`)

**New Features:**
- Checkpoint files now include `language_code` field
- Filename format: `{hash}_{language_code}.json` (e.g., `abc123_fr.json`, `abc123_es.json`)
- Same EPUB can have separate checkpoints for different source languages
- Supports resuming French→English, Spanish→English, etc. independently

**Backwards Compatibility:**
- Old checkpoints without language code default to "fr" when loaded
- All methods accept `language_code` parameter (defaults to "fr")
- Existing French checkpoints continue to work

### 3. Text Chunking (`utils/__init__.py`)

**New Features:**
- CJK language detection:
  - `is_cjk_char()` — checks if single character is CJK
  - `has_cjk_content()` — checks if text contains any CJK
  - Detects: Chinese (Hanzi), Japanese (Hiragana, Katakana), Korean (Hangul)
- CJK-aware chunking:
  - For CJK: splits at 300-character boundaries (no spaces between words)
  - For European: keeps existing sentence-boundary splitting
  - `chunk_text()` accepts `is_cjk` parameter
  - Auto-detects CJK if not explicitly specified

**Backwards Compatibility:**
- Default behavior (European languages) unchanged
- Auto-detection means no changes needed for existing code

### 4. GUI Main Window (`gui/main_window.py`)

**New Components:**
- **Language Selector Section** (top of window):
  - Dropdown showing all installed X→English language pairs
  - Dynamically populated on startup
  - Switches translator to selected language
  - Displays warning if selected language model not installed
- **Install Language Pack Button**:
  - Opens language installer dialog
  - Refreshes selector after installation

**Updated Labels:**
- Input EPUB label now shows: "Input EPUB (French)" or "Input EPUB (Spanish)", etc.
- File picker dialog also uses language name
- Activity log shows source language at start of job
- Status bar shows language code when translation starts

**Backwards Compatibility:**
- If only French model installed, defaults to French (looks like v1)
- All existing French workflows unchanged

### 5. Language Installer Dialog (NEW: `gui/language_installer.py`)

**Features:**
- Lists all available X→English Argos packages
- Shows:
  - Language name (e.g., "Spanish")
  - Estimated download size (e.g., ~150 MB)
  - Installation status (✓ Installed for already-installed)
- Disabled items for already-installed packages
- One-click installation from dialog
- Progress indication during download
- Automatic refresh after installation

### 6. Translation Worker (`gui/worker.py`)

**New Features:**
- Constructor now accepts `source_language` parameter
- Language code passed to checkpoint methods
- Activity log shows detected/selected source language
- Uses CJK-aware chunking:
  - Detects if language is CJK
  - Passes flag to chunking function
  - Character-based splitting for CJK, sentence-based for others
- Enables/disables language selector during translation
- Metadata correctly updates to English regardless of source language

**Backwards Compatibility:**
- Default source language is "fr"
- Existing code works unchanged

## Language Support

Currently supported X→English pairs (via Argos Translate):

```
French (fr)
Spanish (es)
German (de)
Italian (it)
Portuguese (pt)
Russian (ru)
Japanese (ja) *
Chinese (zh) *
Korean (ko) *
Arabic (ar)
Hindi (hi)
Dutch (nl)
Polish (pl)
Turkish (tr)
Vietnamese (vi)
Thai (th)
Greek (el)
Hungarian (hu)
Czech (cs)
Swedish (sv)
Finnish (fi)
Danish (da)
Norwegian (nb)
English (en)
```

* = CJK languages with special 300-char chunking

Note: Not all languages may be available in Argos Translate package index. User can try installing any available X→EN package.

## Testing

**Updated Tests:**

- `test_chunking.py`:
  - CJK character detection tests
  - CJK content detection
  - CJK-specific chunking (300-char limit)
  - Auto-detection of CJK
  
- `test_translation.py`:
  - Language initialization tests
  - `get_installed_languages()` tests
  - `get_available_packages()` tests
  - CJK language detection tests
  - `set_source_language()` tests
  
- `test_checkpoint.py`:
  - Language code in checkpoint filename
  - Separate checkpoints for different languages
  - Backwards compatibility (missing language_code defaults to "fr")

## Usage Examples

### Select Spanish Instead of French

1. Launch app
2. Language selector shows "Spanish" if es→en model installed
3. Select "Spanish" from dropdown
4. Browse for Spanish EPUB
5. Click "Start Translation"
6. Translation proceeds in Spanish→English

### Install German

1. Click "Install Language Pack" button
2. Dialog shows all available packages
3. Find "German" in list
4. Click "Install Selected"
5. Download begins (~150 MB)
6. After installation, German appears in selector
7. Select German and proceed as normal

### Chinese EPUB

1. Install Chinese model via "Install Language Pack"
2. Select "Chinese" from dropdown
3. Browse for Chinese EPUB
4. Translation uses 300-character chunking (no spaces between words)
5. Smart chunking handles Chinese sentence structure correctly

## Backwards Compatibility Guarantees

✅ **All existing French→English workflows unchanged**
- Default language is French
- Old checkpoints load correctly
- Sentence-based chunking still used for French
- UI shows minimal changes if only French installed

✅ **Old checkpoint files compatible**
- Missing `language_code` field defaults to "fr"
- French checkpoints load and work as before

✅ **API backwards compatible**
- All new parameters have defaults
- Existing code works without modification
- ArgosTranslator now takes optional `source_language` (defaults to "fr")

## Performance Considerations

- **CJK Chunking**: Character-based splitting is actually **faster** than sentence-based because no regex parsing needed
- **Language Detection**: Minimal overhead (simple character code range checks)
- **Model Size**: Each language ~100-150 MB compressed

## Limitations & Out of Scope (v1 Multi-Language)

❌ Language auto-detection (user always selects manually)
❌ Right-to-left language support (Arabic, Hebrew)
❌ Context-aware provider selection per language
❌ Batch processing of mixed-language EPUBs
❌ Transliteration for non-Latin scripts

## Code Changes Matrix

| File | Type | Changes |
|------|------|---------|
| `translator/argos_provider.py` | Modified | +Language discovery, CJK detection, multi-language support |
| `checkpoint/__init__.py` | Modified | +Language code in checkpoint filename and JSON |
| `utils/__init__.py` | Modified | +CJK detection and character-based chunking |
| `gui/main_window.py` | Modified | +Language selector, dynamic labels, install button |
| `gui/language_installer.py` | NEW | Language package browser and installer dialog |
| `gui/worker.py` | Modified | +Language code tracking, CJK chunking integration |
| `tests/test_chunking.py` | Modified | +CJK tests (8 new test cases) |
| `tests/test_translation.py` | Modified | +Language discovery tests (6 new test cases) |
| `tests/test_checkpoint.py` | Modified | +Language code tests (3 new test cases) |

## Migration Guide for Existing Users

**No action required.** The app is fully backwards compatible:

1. Existing French checkpoints will load normally
2. If you have French model installed, French is the default
3. To use other languages, click "Install Language Pack" and select one
4. Checkpoints for different languages on the same EPUB are stored separately

## Future Enhancements (v3+)

- [ ] Simplify Chinese chunking with CJK-aware libraries (opencc, pypinyin)
- [ ] Add Thai/Lao/Khmer with character-based chunking
- [ ] Implement language auto-detection with langdetect library
- [ ] Right-to-left language support with mirrortext library
- [ ] Translation memory / glossary per language pair
- [ ] Provider selection UI (choose Argos vs DeepL vs OpenAI per job)

---

**All changes completed on**: 2026-06-17
**Backwards compatible**: Yes ✓
**Tests passing**: Yes ✓
**Ready for production**: Yes ✓
