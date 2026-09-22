# DeskConvert

> **Local Desktop File Converter**  
> A 100% offline Windows desktop application for PDF and image
> conversion, built and maintained by **Muhammad Kamal**.

---

## Download

> **No Python required. No setup. Just install and run.**

| Download | Details |
| :--- | :--- |
| **[DeskConvert_Setup.exe](../../releases/latest)** | Windows 10/11 — 64-bit |

**The installer automatically handles:**
- DeskConvert application
- Tesseract OCR (for the OCR feature)
- Poppler (for PDF processing)
- Desktop shortcut and Start Menu entry

---

## Overview

**DeskConvert** is a privacy-first, fully offline desktop utility
for converting, merging, splitting, compressing, and OCR-processing
PDF and image files — without uploading your data to any website,
server, or third-party service.

Built with a strict file-safety architecture: original source files
are read-only and never modified. All processing runs through a
hidden OS-level staging cache, and every export is non-destructive
with automatic safe-naming to guarantee zero overwrites.

---

## Features

| Feature | Details |
| :--- | :--- |
| **PDF → Image** | Extract pages as JPG or PNG at Screen (72), Print (300), or Custom DPI |
| **Image → PDF** | Lossless image-to-PDF with smart DPI-aware page sizing |
| **Merge Files** | Combine multiple PDFs, images, or mixed files into one PDF |
| **Split PDF** | Extract page ranges (single or individual files) with multi-range support |
| **Batch Convert** | Convert entire folders of images between formats in one operation |
| **OCR** | Scanned PDF → Searchable PDF or plain text file via Tesseract |
| **Compression** | Target-size compression with live suggestion and batch mode |
| **Watermark** | Auto-applied branding on all outputs (toggleable, OCR excluded) |
| **Metadata Control** | Keep or strip EXIF, author, and timestamp data from outputs |
| **History Panel** | Quick-reload last 10 files with missing-file detection |
| **Preview Modal** | Full-resolution page preview before export |

---

## Architecture

```text
[ main.py — Entry Point ]
          │
          ├──► CacheManager (core/cache_manager.py)
          │      └── Stages files to OS temp dir via tempfile.mkdtemp()
          │      └── Generates low-res thumbnails for UI display
          │      └── Clears cache on app exit
          │
          ├──► Processing Engines (core/)
          │      ├── pdf_engine.py     — PyMuPDF: merge, split, PDF→image
          │      ├── image_engine.py   — Pillow: format conversion, batch
          │      ├── ocr_engine.py     — pdf2image + Tesseract: OCR pipeline
          │      ├── watermark.py      — PyMuPDF + Pillow: watermark stamp
          │      ├── metadata.py       — EXIF keep/strip
          │      ├── compression.py    — Binary search quality targeting
          │      └── export.py         — Safe naming, folder routing
          │
          ├──► Background Workers (workers/)
          │      └── QThread subclasses — UI never freezes during processing
          │
          ├──► UI Layer (ui/)
          │      ├── main_window.py    — Root window, signal wiring
          │      ├── center_panel.py   — Drag-drop zone + storyboard grid
          │      ├── right_panel.py    — Actions, compression, page selection
          │      ├── left_panel.py     — Collapsible history panel
          │      ├── thumbnail_widget.py — Draggable page cards with preview
          │      ├── preview_modal.py  — Full-res page preview dialog
          │      ├── settings_dialog.py — DPI, watermark, metadata, output dir
          │      ├── notifications.py  — Non-crashing error/info dialogs
          │      └── status_bar.py     — Operation, file count, export path
          │
          └──► Utilities (utils/)
                 ├── settings.py   — QSettings (Windows Registry persistence)
                 ├── history.py    — 10-item history manager
                 └── validators.py — File type, password, compression checks
```

---

## Module Map

| Module | Responsibility |
| :--- | :--- |
| `core/cache_manager.py` | File staging, thumbnail generation, cache lifecycle |
| `core/pdf_engine.py` | All PDF read/write operations via PyMuPDF |
| `core/image_engine.py` | Image format conversion via Pillow |
| `core/ocr_engine.py` | OCR pipeline — searchable PDF and text extraction |
| `core/watermark.py` | Watermark application for PDF and image outputs |
| `core/metadata.py` | EXIF and PDF metadata keep/strip operations |
| `core/compression.py` | Binary-search quality targeting for size compression |
| `core/export.py` | Safe output naming and directory routing |
| `workers/*.py` | QThread workers — non-blocking background processing |
| `ui/main_window.py` | Root orchestrator — layout, signals, worker dispatch |
| `utils/settings.py` | QSettings wrapper — Windows Registry persistence |
| `utils/history.py` | History list management with file existence checks |
| `utils/validators.py` | File type detection and compression constraint checks |

---

## Prerequisites

- **Python 3.10+**
- **Poppler for Windows** (required by pdf2image)  
  Download: <https://github.com/oschwartz10612/poppler-windows/releases>
  Add the `bin/` folder to your system PATH.
- **Tesseract OCR** (required for OCR feature)  
  Download: <https://github.com/UB-Mannheim/tesseract/wiki>
  Add the install directory to your system PATH.

---

## Installation

### Option A — Windows Installer (Recommended)

Download `DeskConvert_Setup.exe` from the 
[Releases](../../releases/latest) page and run it.
No Python, no dependencies, no configuration required.

### Option B — Run from Source (Developers)

**Prerequisites:**
- Python 3.10+
- Poppler for Windows — add `bin/` to PATH  
  https://github.com/oschwartz10612/poppler-windows/releases
- Tesseract OCR — add to PATH  
  https://github.com/UB-Mannheim/tesseract/wiki

**Steps:**

    git clone https://github.com/muhammad-kamal-asif/deskconvert.git
    cd deskconvert
    python -m venv .venv
    .venv\Scripts\activate
    pip install -r requirements.txt
    python main.py

---

## Supported Formats

**Input:** PDF, JPG, JPEG, PNG, WebP, BMP, TIFF  
**Output:** PDF, JPG, PNG, WebP, BMP, TIFF, TXT (OCR)

---

## Releases

| Version | Date | Notes |
| :--- | :--- | :--- |
| v1.0 | September 2026 | Initial public release |

---

## Author

- **Developer**: Muhammad Kamal
- **GitHub**: [muhammad-kamal-asif](https://github.com/muhammad-kamal-asif)
- **Project Type**: Personal utility tool (portfolio project)
- **License**: MIT
