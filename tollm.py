# project_to_markdown.py

import os
import argparse
import chardet # Optional: for better encoding detection. Install with: pip install chardet

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
    '.c': 'c',
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
    try:
        with open(file_path, 'rb') as f:
            raw_data = f.read(5000) # Read first 5KB to guess encoding
            result = chardet.detect(raw_data)
            encoding = result['encoding']
            # Provide default if detection fails or is uncertain
            return encoding if encoding else 'utf-8'
    except Exception:
        return 'utf-8' # Fallback to utf-8 on any error

def get_file_content(file_path):
    """Read content of a file, trying different encodings."""
    try:
        # Try preferred encoding first
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    except UnicodeDecodeError:
        print(f"Warning: UTF-8 decoding failed for {file_path}. Trying detected encoding...")
        try:
            # Try detecting encoding (requires chardet)
            encoding = detect_encoding(file_path)
            print(f"Detected encoding: {encoding}")
            with open(file_path, 'r', encoding=encoding) as f:
                return f.read()
        except (UnicodeDecodeError, TypeError, LookupError) as e:
             # Fallback: try latin-1 or ignore errors
            print(f"Warning: Decoding failed for {file_path} with detected encoding {encoding}. Error: {e}. Trying latin-1...")
            try:
                with open(file_path, 'r', encoding='latin-1') as f:
                    return f.read()
            except Exception as final_e:
                print(f"Error: Could not read file {file_path}. Skipping. Reason: {final_e}")
                return None
    except IOError as e:
        print(f"Error: Could not read file {file_path}. Skipping. Reason: {e}")
        return None
    except Exception as e:
        print(f"Error: An unexpected error occurred while reading {file_path}. Skipping. Reason: {e}")
        return None


def process_directory(input_dir, output_file):
    """
    Traverse input directory, read specified files, and write to output file.
    """
    if not os.path.isdir(input_dir):
        print(f"Error: Input directory '{input_dir}' not found or is not a directory.")
        return

    abs_input_dir = os.path.abspath(input_dir)
    output_content = []

    print(f"Starting scan of directory: {abs_input_dir}")

    for root, dirs, files in os.walk(abs_input_dir, topdown=True):
        # --- Directory Exclusion ---
        # Modify dirs in-place to prevent os.walk from traversing excluded directories
        dirs[:] = [d for d in dirs if d not in EXCLUDED_DIRECTORIES]

        rel_dir = os.path.relpath(root, abs_input_dir)
        if rel_dir == '.':
            rel_dir = '' # Avoid './' prefix for root files

        print(f"Processing directory: {os.path.join(input_dir, rel_dir) if rel_dir else input_dir}")

        for filename in files:
            # --- File Exclusion ---
            file_path = os.path.join(root, filename)
            rel_file_path = os.path.join(rel_dir, filename) if rel_dir else filename
            _ , extension = os.path.splitext(filename)

            # Check against excluded files/extensions
            if filename in EXCLUDED_FILES_OR_EXTENSIONS or extension.lower() in EXCLUDED_FILES_OR_EXTENSIONS:
                print(f"  Skipping excluded file: {rel_file_path}")
                continue

            # Handle files without extension (like Dockerfile)
            is_includable_no_ext = filename in INCLUDED_EXTENSIONS
            is_includable_ext = extension.lower() in INCLUDED_EXTENSIONS

            # --- File Inclusion ---
            if not is_includable_ext and not is_includable_no_ext:
                print(f"  Skipping non-included file type: {rel_file_path}")
                continue

            # --- Read and Format File Content ---
            print(f"  Processing file: {rel_file_path}")
            content = get_file_content(file_path)

            if content is not None:
                # Determine language for Markdown code block
                lang_key = extension.lower() if is_includable_ext else filename # Use filename if no ext (e.g., Dockerfile)
                language = LANGUAGE_MAP.get(lang_key, '') # Default to empty (plain text)

                # Format for Markdown
                output_content.append(f"--- File: {rel_file_path.replace(os.sep, '/')} ---\n") # Use forward slashes for consistency
                output_content.append(f"```{language}\n")
                output_content.append(content)
                # Ensure the code block fence is on a new line if the content doesn't end with one
                if not content.endswith('\n'):
                    output_content.append('\n')
                output_content.append("```\n\n") # Add extra newline for spacing

    # --- Write Output File ---
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write("".join(output_content))
        print(f"\nSuccessfully created context file: {os.path.abspath(output_file)}")
        # Provide size information
        try:
            file_size = os.path.getsize(output_file)
            print(f"Output file size: {file_size / 1024:.2f} KB")
            if file_size > 500 * 1024: # Example threshold: 500KB
                 print("Warning: Output file is large. It might exceed LLM context limits.")
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
        default="project_context.txt",
        help="Path to the output text file (default: project_context.txt in the current directory)."
    )
    parser.add_argument(
        "--no-chardet",
        action="store_true",
        help="Disable chardet for encoding detection (will rely on utf-8 and latin-1 fallbacks)."
    )


    args = parser.parse_args()

    # Conditionally import chardet if not disabled
    if not args.no_chardet:
        try:
            import chardet
        except ImportError:
            print("Warning: 'chardet' library not found. Encoding detection will be limited.")
            print("Install it with: pip install chardet")
            # Fallback to not using chardet
            detect_encoding = lambda fp: 'utf-8' # Define a dummy function
    else:
        # Define a dummy function if explicitly disabled
        detect_encoding = lambda fp: 'utf-8'


    process_directory(args.input_dir, args.output)
