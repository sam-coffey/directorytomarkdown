# Project Code to Markdown Context

A simple Python script to recursively scan a developer project directory and combine the contents of relevant code/text files into a single Markdown-formatted text file. This output is optimized for pasting into Large Language Model (LLM) prompts as context.

## Features

* **Recursive Scan:** Traverses the entire specified project directory including subdirectories.
* **Configurable File Inclusion:** Processes only files with specified extensions (e.g., `.py`, `.js`, `.html`, `.css`, `.md`). Easily customizable.
* **Configurable Exclusion:** Ignores specified directories (e.g., `.git`, `node_modules`, `venv`) and file types (e.g., `.log`, binaries, images, lock files). Easily customizable.
* **LLM-Optimized Markdown:**
    * Clearly marks the beginning of each file with its relative path (`--- File: path/to/file.ext ---`).
    * Wraps file content in Markdown fenced code blocks (``` ```).
    * Attempts to add the correct language identifier (e.g., ```python`) based on file extension for syntax highlighting awareness by the LLM.
* **Single Output File:** Consolidates all content into one `.txt` file.
* **Encoding Detection:** Uses `chardet` (if available) to handle files with encodings other than UTF-8, with fallbacks.
* **Command-Line Interface:** Easy to use via command-line arguments for input directory and output file path.

## Requirements

* Python 3.x
* `chardet` library (optional, but recommended for better encoding support):
    ```bash
    pip install chardet
    ```

## Usage

1.  Save the script as `project_to_markdown.py` (or your preferred name).
2.  Open your terminal or command prompt.
3.  Run the script, providing the path to your project directory.

**Basic Usage (output to `project_context.txt`):**

```bash
python directorytomarkdown.py /path/to/your/project
