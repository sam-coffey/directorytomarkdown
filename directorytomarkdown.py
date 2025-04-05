# project_to_markdown.py

import os
import argparse
try:
    import chardet # Optional: for better encoding detection. Install with: pip install chardet
    _CHARDET_AVAILABLE = True
except ImportError:
    _CHARDET_AVAILABLE = False
    print("Warning: 'chardet' library not found. Encoding detection will be limited to utf-8/latin-1.")
    print("Install it with: pip install chardet")

# --- Configuration ---

# Add file extensions you want to include.
# Common code/text file extensions:
INCLUDED_EXTENSIONS = {
    '.py', '.js', '.jsx', '.ts', '.tsx', '.html', '.htm', '.css', '.scss',
    '.java', '.kt', '.swift', '.c', '.cpp', '.h', '.hpp', '.cs', '.go',
    '.php', '.rb', '.pl', '.sh', '.bat', '.ps1',
    '.json', '.yaml', '.yml', '.xml', '.toml', '.ini', '.cfg',
    '.md', '.txt', '.rst', '.tex',
    '.sql', '.dockerfile', 'Dockerfile', '.env', '.gitignore', '.gitattributes',
    # Add or remove as needed
}

# Add directory names to completely ignore.
EXCLUDED_DIRECTORIES = {
    '.git', 'node_modules', 'venv', '.venv', 'env', '.env',
    '__pycache__', 'dist', 'build', 'target', 'out',
    '.vscode', '.idea', '.project', '.settings',
    'vendor', 'Pods', 'Carthage',
    # Add or remove as needed
}

# Add specific file names or extensions to ignore.
EXCLUDED_FILES_OR_EXTENSIONS = {
    '.log', '.tmp', '.temp', '.swp', '.bak', '.old',
    '.DS_Store', 'Thumbs.db',
    '.lock', 'package-lock.json', 'yarn.lock', 'composer.lock', 'Pipfile.lock',
    # Binary file types (usually not useful for LLM context)
    '.png', '.jpg', '.jpeg', '.gif', '.bmp', '.ico', '.svg',
    '.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx',
    '.zip', '.tar', '.gz', '.rar', '.7z',
    '.exe', '.dll', '.so', '.dylib', '.jar', '.class', '.pyc', '.o',
    '.mp3', '.wav', '.mp4', '.mov', '.avi',
    # Add or remove as needed
}

# Mapping from file extension to Markdown language identifier
LANGUAGE_MAP = {
    '.py': 'python',
    '.js': 'javascript',
    '.jsx': 'jsx',
    '.ts': 'typescript',
    '.tsx': 'tsx',
    '.html': 'html',
    '.htm': 'html',
    '.css': 'css',
    '.scss': 'scss',
    '.java': 'java',
    '.kt': 'kotlin',
    '.swift': 'swift',
    '.c': 'c', # Often C or C++, default to C
    '.cpp': 'cpp',
    '.h': 'c', # Often C or C++, default to C
    '.hpp': 'cpp',
    '.cs': 'csharp',
    '.go': 'go',
    '.php': 'php',
    '.rb': 'ruby',
    '.pl': 'perl',
    '.sh': 'bash',
    '.bat': 'batch',
    '.ps1': 'powershell',
    '.json': 'json',
    '.yaml': 'yaml',
    '.yml': 'yaml',
    '.xml': 'xml',
    '.toml': 'toml',
    '.ini': 'ini',
    '.cfg': 'ini', # Often INI format
    '.md': 'markdown',
    '.txt': 'text',
    '.rst': 'rst',
    '.tex': 'latex',
    '.sql': 'sql',
    '.dockerfile': 'dockerfile',
    'Dockerfile': 'dockerfile', # Handle files named 'Dockerfile'
    '.env': 'text', # Often just key-value pairs
    '.gitignore': 'text',
    '.gitattributes': 'text',
    # Add more mappings if needed
}

def detect_encoding(file_path):
    """Detect file encoding using chardet, fallback to utf-8."""
    if not _CHARDET_AVAILABLE:
        return 'utf-8' # Chardet not available, return default

    try:
        with open(file_path, 'rb') as f:
            raw_data = f.read(5000) # Read first 5KB to guess encoding
            if not raw_data: # Handle empty files
                 return 'utf-8'
            result = chardet.detect(raw_data)
            encoding = result['encoding']
            confidence = result['confidence']
            # Provide default if detection fails or is uncertain (e.g., < 70% confidence)
            # Adjust confidence threshold as needed
            return encoding if encoding and confidence > 0.7 else 'utf-8'
    except Exception as e:
        print(f"Warning: Encoding detection failed for {file_path}. Error: {e}. Falling back to utf-8.")
        return 'utf-8' # Fallback to utf-8 on any error

def get_file_content(file_path):
    """Read content of a file, trying different encodings."""
    encodings_to_try = ['utf-8']
    detected_encoding = detect_encoding(file_path)
    if detected_encoding not in encodings_to_try:
        encodings_to_try.append(detected_encoding)
    # Add latin-1 as a common fallback
    if 'latin-1' not in encodings_to_try:
        encodings_to_try.append('latin-1')

    last_exception = None
    for encoding in encodings_to_try:
        try:
            with open(file_path, 'r', encoding=encoding) as f:
                return f.read()
        except UnicodeDecodeError as e:
            last_exception = e
            # print(f"Debug: Failed to decode {file_path} with {encoding}.") # Optional debug print
            continue # Try next encoding
        except (IOError, OSError) as e:
            print(f"Error: Could not read file {file_path}. Skipping. Reason: {e}")
            return None
        except Exception as e: # Catch other potential file reading errors
            print(f"Error: An unexpected error occurred while reading {file_path} with encoding {encoding}. Skipping. Reason: {e}")
            return None

    # If all attempts failed
    print(f"Error: Could not decode file {file_path} with tried encodings: {encodings_to_try}. Skipping. Last error: {last_exception}")
    return None


def create_llm_header(input_dir_abs_path):
    """Creates the standard header message for the LLM."""
    header = f"""# Project Code Context for LLM

**Input Directory Scanned:** `{input_dir_abs_path}`

**Purpose:** This document aggregates source code and relevant text files from the specified software project directory. It is intended to provide context for a Large Language Model (LLM) to understand the project.

**Structure:**
* Files are presented sequentially below this header.
* Each file's content is clearly marked with a header line: `--- File: [relative/path/to/file] ---` (paths use forward slashes '/' for consistency).
* The content of each file follows its header, enclosed in a Markdown fenced code block (``` ```).
* The code block is tagged with the inferred programming language or format (e.g., ```python, ```json, ```text) where possible.

**Instructions for LLM:** Please analyze the following file contents to understand the project's structure, functionality, code logic, and configuration. Use this information to answer questions or perform tasks related to this project.

---
"""  # Horizontal rule to separate header from file content
    return header


def process_directory(input_dir, output_file):
    """
    Traverse input directory, read specified files, and write to output file
    with an introductory LLM header.
    """
    if not os.path.isdir(input_dir):
        print(f"Error: Input directory '{input_dir}' not found or is not a directory.")
        return

    abs_input_dir = os.path.abspath(input_dir)

    # --- Create LLM Header ---
    llm_header = create_llm_header(abs_input_dir)
    output_content = [llm_header] # Initialize the list with the header

    print(f"Starting scan of directory: {abs_input_dir}")

    # Use a set to track processed files to avoid duplicates if symlinks create loops (though EXCLUDED_DIRECTORIES helps)
    processed_files = set()

    for root, dirs, files in os.walk(abs_input_dir, topdown=True, followlinks=False): # Avoid following symlinks by default
        # --- Directory Exclusion ---
        # Modify dirs in-place to prevent os.walk from traversing excluded directories
        dirs[:] = [d for d in dirs if d not in EXCLUDED_DIRECTORIES and not d.startswith('.')] # Also exclude hidden dirs

        rel_dir = os.path.relpath(root, abs_input_dir)
        if rel_dir == '.':
            rel_dir = '' # Avoid './' prefix for root files

        print(f"Processing directory: {os.path.join(input_dir, rel_dir) if rel_dir else input_dir}")

        # Sort files for consistent order
        files.sort()

        for filename in files:
            file_path = os.path.join(root, filename)
            abs_file_path = os.path.abspath(file_path)

            # Skip if already processed (handles potential symlink complexities if followlinks=True)
            if abs_file_path in processed_files:
                continue

            # Basic check for symlink loops, although followlinks=False is primary protection
            if os.path.islink(file_path):
                 print(f"  Skipping symlink: {filename}")
                 continue

            # Ensure it's actually a file
            if not os.path.isfile(file_path):
                 continue

            rel_file_path = os.path.join(rel_dir, filename) if rel_dir else filename
            _ , extension = os.path.splitext(filename)
            extension_lower = extension.lower() # Normalize extension

            # --- File Exclusion ---
            # Check against excluded files/extensions
            if (filename in EXCLUDED_FILES_OR_EXTENSIONS or
                (extension_lower and extension_lower in EXCLUDED_FILES_OR_EXTENSIONS)):
                print(f"  Skipping excluded file/type: {rel_file_path}")
                continue

            # Handle files without extension (like Dockerfile) or specific included names
            is_includable_name = filename in INCLUDED_EXTENSIONS
            # Check if the normalized extension is included
            is_includable_ext = extension_lower in INCLUDED_EXTENSIONS

            # --- File Inclusion ---
            if not is_includable_ext and not is_includable_name:
                print(f"  Skipping non-included file type: {rel_file_path}")
                continue

            # --- Read and Format File Content ---
            print(f"  Processing file: {rel_file_path}")
            content = get_file_content(file_path)

            if content is not None:
                processed_files.add(abs_file_path) # Mark as processed

                # Determine language for Markdown code block
                # Prioritize filename check (like 'Dockerfile'), then extension
                lang_key = filename if is_includable_name else extension_lower
                language = LANGUAGE_MAP.get(lang_key, '') # Default to empty (plain text)

                # Format for Markdown - use forward slashes in paths for consistency
                path_for_display = rel_file_path.replace(os.sep, '/')
                output_content.append(f"--- File: {path_for_display} ---\n")
                output_content.append(f"```{language}\n")
                output_content.append(content)
                # Ensure the code block fence is on a new line if the content doesn't end with one
                if content and not content.endswith('\n'): # Check if content is not empty
                    output_content.append('\n')
                output_content.append("```\n\n") # Add extra newline for spacing

    # --- Write Output File ---
    if not output_content: # Should not happen if header is always added, but safety check
        print("Warning: No content was processed.")
        return

    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write("".join(output_content)) # Write header and all file contents
        print(f"\nSuccessfully created context file: {os.path.abspath(output_file)}")
        # Provide size information
        try:
            file_size = os.path.getsize(output_file)
            print(f"Output file size: {file_size / 1024:.2f} KB ({file_size:,} bytes)")
            # Adjust warning threshold as needed (e.g., based on typical LLM limits)
            # Anthropic Claude 3 Opus/Sonnet: ~200k tokens (~600-800KB text?)
            # GPT-4 Turbo: 128k tokens (~400-500KB text?)
            # Gemini 1.5 Pro: 1M tokens (Massive)
            # Conservative warning threshold:
            warn_threshold_kb = 750
            if file_size > warn_threshold_kb * 1024:
                 print(f"Warning: Output file is large (> {warn_threshold_kb} KB). It might exceed the context limit of some LLMs.")
        except OSError:
            pass # Ignore if size check fails
    except IOError as e:
        print(f"\nError: Could not write to output file '{output_file}'. Reason: {e}")
    except Exception as e:
        print(f"\nError: An unexpected error occurred while writing the output file. Reason: {e}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Combine code files from a project directory into a single Markdown-formatted text file for LLM context.",
        formatter_class=argparse.RawTextHelpFormatter # Keep newlines in help message
    )
    parser.add_argument(
        "input_dir",
        help="Path to the project directory to scan."
    )
    parser.add_argument(
        "-o", "--output",
        default="project_context.md", # Changed default extension to .md
        help="Path to the output Markdown file (default: project_context.md in the current directory)."
    )
    # Removed --no-chardet as chardet is now conditionally handled
    # You could add it back if you want an explicit way to disable even if installed

    args = parser.parse_args()

    # No need for conditional import here anymore, handled at the top.
    # The detect_encoding function will adapt based on _CHARDET_AVAILABLE.

    process_directory(args.input_dir, args.output)