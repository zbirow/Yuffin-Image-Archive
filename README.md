# Yuffin Archive Format ⚡
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/)
[![JavaScript](https://img.shields.io/badge/JavaScript-ES6+-yellow.svg)](https://developer.mozilla.org/en-US/docs/Web/JavaScript)

**Blazing fast image archive format with instant web access** - 4GB archives load in 1 second! ⚡

**A high-performance, lightweight binary archive for your photo collections, complete with a GUI packer and a serverless web-based gallery viewer.**

This project provides a complete toolkit for efficiently storing and browsing large numbers of images. It uses a custom, highly-optimized binary format (`.yuf`) to pack entire directory structures into a single, portable file.

_The cross-platform GUI Packer tool._

![](https://github.com/zbirow/Yuffin-Archive/blob/main/scs1.png)

_The feature-rich, serverless [Web Viewer](https://zbirow.github.io/Yuffin-Archive/)._
![](https://github.com/zbirow/Yuffin-Archive/blob/main/scs2.png)

## ⚡ Performance Benchmark
| Format | 4GB Archive Load | Random Access | Web Ready |
|--------|------------------|---------------|-----------|
| **Yuffin** | ✅ **1 second** | ✅ **Instant** | ✅ **Yes** |
| ZIP | ❌ 20-30 seconds | ❌ Slow | ❌ No |
| TAR | ❌ 15-25 seconds | ❌ Very Slow | ❌ No |

## 🎯 Use Cases
- Web comics/manga viewers
- Image galleries with thousands of images  
- Game asset bundles


## ✨ Core Features

*   **Highly Optimized Binary Format:** The custom `.yuf` format is designed for minimal size and extremely fast, on-demand data access.
*   **Directory Structure Preservation:** Archives maintain the original folder hierarchy, allowing for organized collections.(File names are not preserved. After unpacking, they take the form: image_*)
*   **Large File Support:** Optimized to handle large archives (up to 4GB) without loading the entire file into memory.
*   **Cross-Platform GUI Packer:** An easy-to-use tool built with Python and Tkinter to pack and unpack archives. It runs on Windows, macOS, and Linux.
*   **Serverless Web Viewer:** A single, self-contained HTML file that can open and browse `.yuf` archives directly in your web browser. No backend or server required!
*   **Advanced Viewer Features:**
    *   **Lazy Loading:** Only images currently on-screen are loaded, ensuring smooth performance even with thousands of photos.
    *   **Directory Filtering:** Instantly filter the gallery by the original folder structure.
    *   **Full Pagination:** Complete navigation controls, including "First," "Last," "Next," "Previous," and a "Go to page" input.
    *   **Lightbox:** Click any thumbnail to view a full-sized version of the image.
    *   **Comic Book View:**
        *   Seamless reading experience with continuous vertical flow
        *   Smart chapter detection and navigation (supports fractional chapters like 65.5, 90.1, etc.)
        *   Chapter navigation buttons at both top and bottom of the page
        *   Automatic scrolling to top when changing chapters
        *   No gaps between images for authentic comic book reading
        *   Perfect for comics, manga, and other sequential art


## 📁 Directory Naming for Comic View
 For optimal compatibility with the comic book view feature, please use the following naming pattern for directories containing chapters:

**Standard format:** chapter_X where X is the chapter number

**Examples:** chapter_1, chapter_2, chapter_15

**Fractional chapters supported:** chapter_65.5, chapter_90.1, chapter_90.2

The viewer will automatically:

 * Detect and sort chapters numerically

 * Handle fractional chapter numbers correctly

 * Provide seamless navigation between chapters in comic book view



## 🛠️ Components

1.  **The Packer (`Yuffin-Archive.py`)**
    A Python application with a graphical user interface for creating (`.yuf`) archives from a folder of images and for unpacking them back into their original directory structure.

2.  **The Viewer (`index.html`)**
    A powerful, client-side web application written in pure JavaScript. It can open a local `.yuf` file, parse its structure, and display an interactive, filterable, and paginated gallery.

## 🚀 How to Use

### Packing & Unpacking Images

1.  Make sure you have Python installed on your system.
2.  Run the `Yuffin-Archive.py` file.
3.  **To Pack:**
    *   Click "Browse..." to select your source folder containing images.
    *   Click "Save As..." to choose a location and name for your `.yuf` archive.
    *   Click **PACK**.
4.  **To Unpack:**
    *   Click "Browse..." to select an existing `.yuf` archive file.
    *   Click "Browse..." to choose an empty output folder.
    *   Click **UNPACK**.

### Viewing an Archive

1.  Open the `index.html` file in any modern web browser (Chrome, Firefox, Edge, Safari).
2.  Click the "Select .yuf File" button.
3.  Select your `.yuf` archive file from your computer.
4.  The gallery will load instantly. Use the filter and pagination controls to browse your collection.

## ⚙️ The `.yuf` File Format

The file format is designed for efficiency and random access.

| Section             | Description                                                                                             |
| ------------------- | ------------------------------------------------------------------------------------------------------- |
| **Header (38 bytes)** | Contains magic number (`Yuffin`), version, file/dir counts, and offsets to the main data tables.      |
| **Directory Table** | A NULL-terminated list of all unique directory paths, encoded in UTF-8.                                 |
| **File Index**      | A continuous block of 8-byte entries. Each entry contains a 4-byte offset to image data and a 2-byte directory ID. |
| **Data Blocks**     | The actual image data. Each block is prefixed with a `ZBIR` marker and its size, and is 16-byte aligned. |

## 💻 Technology Stack

*   **Packer/Unpacker:** Python, Tkinter (for GUI)
*   **Viewer:** HTML5, CSS3, Vanilla JavaScript (no frameworks, no dependencies)

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
