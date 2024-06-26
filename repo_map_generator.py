import argparse
import fnmatch
import logging
import re
import os
import shutil
import subprocess
import time
from datetime import datetime
from pathlib import Path
from typing import List, Set, Dict, Tuple, Optional

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

EXCLUDE_FILES: Set[str] = {
    # Version Control and Configuration Files
    '.gitignore', '.gitattributes', '.hgignore', '.svnignore',
    'requirements.txt', '*LICENSE*', 'setup.py', 'setup.cfg', 'pyproject.toml', 'Pipfile', 'Pipfile.lock', '*README*',
    'package.json', 'package-lock.json', 'yarn.lock', 'composer.json', 'composer.lock',
    '.editorconfig', '.eslintrc', '.prettierrc', '.stylelintrc',
    # Compiled/Binary Files
    '*.pyc', '*.pyo', '*.pyd', '*.so', '*.dll', '*.exe', '*.obj', '*.o',
    '*.a', '*.lib', '*.egg', '*.whl',
    # Logs and Databases
    '*.log', '*.sql', '*.sqlite', '*.db',
    # System and Temp Files
    '.DS_Store', 'Thumbs.db', 'desktop.ini',
    '*~', '*.swp', '*.swo', '*.tmp', 'temp_*',
    '__init__.py', 'MANIFEST.in',
    'node_modules',
    # IDE and Editor Files
    '*.iml', '*.ipr', '*.iws',
    # Backup and Cache Files
    '*.bak', '*.cache', '*.pid',
    # Image Files
    '*.png', '*.jpg', '*.jpeg', '*.gif', '*.bmp', '*.svg', '*.tiff', '*.ico',
    # Video Files
    '*.mp4', '*.mkv', '*.avi', '*.mov', '*.wmv', '*.flv', '*.webm', '*.m4v',
    # Audio Files
    '*.mp3', '*.wav', '*.flac', '*.aac', '*.ogg', '*.wma', '*.m4a',
    # Document Files
    '*.pdf', '*.doc', '*.docx', '*.ppt', '*.pptx', '*.xls', '*.xlsx', '*.odt', '*.ods',
    # Archive Files
    '*.zip', '*.tar', '*.gz', '*.rar', '*.7z', '*.bz2', '*.xz',
    # Other Media Files
    '*.psd', '*.ai', '*.eps', '*.indd', '*.fla', '*.swf',
    # Custom Project Files
    '*aider*', '*.tree_map.*', 'repo_map.md', 'repo_map_gen*'
}

EXCLUDE_DIRS: Set[str] = {
    # Version Control Directories
    '.git', '.svn', '.hg', 'CVS',
    # Virtual Environment Directories
    'venv', 'env', '.env', 'virtualenv', '.venv',
    '.conda', 'anaconda', 'miniconda',
    # Build and Distribution Directories
    'build', 'dist', 'target', 'out',
    # Python Cache and Testing Directories
    '__pycache__', '.mypy_cache', '.pytest_cache', '.ruff_cache',
    '.tox', '.eggs', '.cache',
    # Node.js and JavaScript Directories
    'node_modules', 'bower_components', 'jspm_packages',
    # Dependency Directories
    'vendor', 'packages',
    # IDE and Editor Directories
    '.idea', '.vscode', '.vs', '.eclipse', '.settings',
    '.sublime-project', '.sublime-workspace',
    # Documentation Directories
    'docs', '_build', 'site', 'sphinx-docs',
    # Coverage and Log Directories
    'htmlcov', '.coverage', '.coveragerc',
    'logs', '__logs__',
    # Temporary Directories
    'tmp', 'temp',
    # System Directories
    '$RECYCLE.BIN', 'System Volume Information',
    # Other Cache and Build Tool Directories
    '.sass-cache', '.gradle', '.m2',
    # Additional Directories
    'media', 'public', 'static', 'assets',
    # Custom Project Directories
    '*aider*', '.tree_map_backup'
}

# Default comment style for unknown file types
DEFAULT_COMMENT_STYLE = ('#', '#', '')

# Comment styles for different file types
COMMENT_STYLES: Dict[str, Tuple[str, str, str]] = {
    # Single-line comment style: (start, middle, end)
    'py': ('#', '#', ''),
    'js': ('//', '//', ''),
    'java': ('//', '//', ''),
    'c': ('//', '//', ''),
    'cpp': ('//', '//', ''),
    'cs': ('//', '//', ''),
    'go': ('//', '//', ''),
    'rs': ('//', '//', ''),
    'swift': ('//', '//', ''),
    'kt': ('//', '//', ''),
    'scala': ('//', '//', ''),
    'rb': ('#', '#', ''),
    'pl': ('#', '#', ''),
    'sh': ('#', '#', ''),
    'bash': ('#', '#', ''),
    'zsh': ('#', '#', ''),
    'yaml': ('#', '#', ''),
    'yml': ('#', '#', ''),
    'toml': ('#', '#', ''),
    'ini': (';', ';', ''),
    'cfg': (';', ';', ''),
    'conf': ('#', '#', ''),
    'sql': ('--', '--', ''),
    'lua': ('--', '--', ''),
    'hs': ('--', '--', ''),
    'md': ('<!--', ' *', '-->'),
    'html': ('<!--', ' *', '-->'),
    'htm': ('<!--', ' *', '-->'),
    'xml': ('<!--', ' *', '-->'),
    'css': ('/*', ' *', '*/'),
    'scss': ('/*', ' *', '*/'),
    'less': ('/*', ' *', '*/'),
    'php': ('/*', ' *', '*/'),
    'jsx': ('/*', ' *', '*/'),
    'tsx': ('/*', ' *', '*/'),
}

class Metrics:
    def __init__(self):
        self.start_time = time.time()
        self.files_processed = 0
        self.files_modified = 0
        self.files_skipped = 0
        self.backup_size = 0
        self.errors = 0
        self.map_file_saved = False
        self.map_file_location: Optional[Path] = None

    def print_summary(self):
        duration = time.time() - self.start_time
        print("\n--- Metrics Summary ---")
        if self.map_file_saved:
            print(f"Map file saved: Yes")
            print(f"Map file location: {self.map_file_location}")
        else:
            print("Map file saved: No")
        print(f"Total files processed: {self.files_processed}")
        print(f"Files modified: {self.files_modified}")
        print(f"Files skipped: {self.files_skipped}")
        print(f"Backup size: {self.backup_size / (1024*1024):.2f} MB")
        print(f"Errors encountered: {self.errors}")
        print(f"Total execution time: {duration:.2f} seconds")

def should_exclude(path: Path, relative_to: Path) -> bool:
    """Check if a file or directory should be excluded (case-insensitive)."""
    relative_path = path.relative_to(relative_to)
    parts = relative_path.parts

    # Check each part of the path against exclusion patterns (case-insensitive)
    for part in parts:
        if any(fnmatch.fnmatch(part.lower(), pattern.lower()) for pattern in EXCLUDE_DIRS):
            return True

    # Check the file name against file exclusion patterns (case-insensitive)
    if path.is_file():
        return any(fnmatch.fnmatch(path.name.lower(), pattern.lower()) for pattern in EXCLUDE_FILES)

    return False

def get_comment_style(file_extension: str) -> Tuple[str, str, str]:
    """Get the appropriate comment style for a given file extension."""
    return COMMENT_STYLES.get(file_extension.lstrip('.'), DEFAULT_COMMENT_STYLE)

def is_binary_file(filepath: Path) -> bool:
    """Check if a file is binary."""
    try:
        with open(filepath, 'tr') as check_file:
            check_file.read()
            return False
    except:
        return True

def update_files_with_tree(startpath: Path, tree: str, backup_dir: Optional[Path]) -> List[Path]:
    modified_files = []
    for filepath in startpath.rglob('*'):
        logger.debug(f"Processing file: {filepath}")
        
        if should_exclude(filepath, startpath):
            logger.info(f"Skipping excluded path: {filepath}")
            metrics.files_skipped += 1
            continue

        if filepath.is_file():
            metrics.files_processed += 1
            
            if is_binary_file(filepath):
                logger.info(f"Skipping binary file: {filepath}")
                metrics.files_skipped += 1
                continue
            
            try:
                backup_successful = True
                if backup_dir:
                    logger.debug(f"Attempting to create backup for: {filepath}")
                    backup_path = create_backup(filepath, backup_dir, startpath)
                    if not backup_path:
                        logger.warning(f"Failed to create backup for {filepath}, proceeding without backup")
                        backup_successful = False
                    else:
                        logger.info(f"Backup created successfully for: {filepath}")

                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()

                comment_start, comment_middle, comment_end = get_comment_style(filepath.suffix)
                
                # Create the updated map as a single unit
                updated_map = f"{comment_start} Repository Map:\n"
                for line in tree.split('\n'):
                    updated_map += f"{comment_middle} {line}\n"
                updated_map += f"{comment_middle} File: {filepath.name}\n"
                if comment_end:
                    updated_map += f"{comment_end}\n"

                # Pattern to match the entire existing map, including the "File:" line
                map_pattern = rf'({re.escape(comment_start)} Repository Map:.*?{re.escape(comment_middle)} File:.*?\n)'
                if comment_end:
                    map_pattern += rf'({re.escape(comment_end)}\s*)'

                if re.search(map_pattern, content, re.DOTALL):
                    # Replace the existing map while preserving all other content
                    updated_content, n = re.subn(map_pattern, updated_map, content, count=1, flags=re.DOTALL)
                    if n == 0:  # If no substitution was made (shouldn't happen, but just in case)
                        updated_content = updated_map + content
                else:
                    # Add the new map at the beginning of the file, preserving all existing content
                    updated_content = updated_map + content

                if updated_content != content:
                    with open(filepath, 'w', encoding='utf-8') as f:
                        f.write(updated_content)
                    modified_files.append(filepath)
                    metrics.files_modified += 1
                    logger.info(f"Updated repo map in {filepath}")
                    if not backup_successful:
                        logger.warning(f"File {filepath} was updated without a backup")
                else:
                    logger.info(f"No changes needed for {filepath}")
                    metrics.files_skipped += 1
            except Exception as e:
                logger.error(f"Error processing {filepath}: {str(e)}")
                metrics.errors += 1
                metrics.files_skipped += 1

    return modified_files

def generate_markdown_map(tree: str, output_file: Path):
    """Generate a Markdown file containing the repository map."""
    try:
        content = f"# Repository Map\n\n```\n{tree}\n```\n"
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(content)
        logger.info(f"Generated Markdown repository map: {output_file}")
    except Exception as e:
        logger.error(f"Error generating Markdown map: {str(e)}")
        metrics.errors += 1

def git_commit_changes(modified_files: List[Path]):
    """Commit changes to git repository, handling long file lists."""
    try:
        # Split the list of files into smaller chunks to avoid command line length limits
        chunk_size = 100  # Adjust this value as needed
        for i in range(0, len(modified_files), chunk_size):
            chunk = modified_files[i:i + chunk_size]
            subprocess.run(["git", "add"] + [str(f) for f in chunk], check=True)
        
        subprocess.run(["git", "commit", "-m", "Update repository map"], check=True)
        logger.info("Changes committed to git repository")
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to commit changes to git: {e}")
        metrics.errors += 1

MAX_PATH_LENGTH = 260  # Increased to a more reasonable limit

def create_backup(filepath: Path, backup_dir: Path, startpath: Path) -> Optional[Path]:
    """Create a backup of the given file."""
    try:
        relative_path = filepath.relative_to(startpath)
        backup_path = backup_dir / relative_path
        
        logger.debug(f"Attempting to create backup for: {filepath}")
        logger.debug(f"Relative path for backup: {relative_path}")
        logger.debug(f"Initial backup path: {backup_path}")

        if '.tree_map_backup' in str(filepath):
            logger.info(f"Skipping backup for file already in backup directory: {filepath}")
            return None
        
        if should_exclude(filepath, startpath):
            logger.info(f"Skipping backup for excluded file: {filepath}")
            return None
        
        if len(str(backup_path)) > MAX_PATH_LENGTH:
            logger.warning(f"Backup path too long for {filepath}. Using alternative backup method.")
            import hashlib
            hash_name = hashlib.md5(str(filepath).encode()).hexdigest()
            backup_path = backup_dir / f"{hash_name}{filepath.suffix}"
        
        logger.debug(f"Final backup path: {backup_path}")
        
        backup_path.parent.mkdir(parents=True, exist_ok=True)
        
        shutil.copy2(filepath, backup_path)
        metrics.backup_size += filepath.stat().st_size
        logger.info(f"Backup created: {backup_path}")
        return backup_path
    except Exception as e:
        logger.error(f"Failed to create backup for {filepath}: {str(e)}")
        metrics.errors += 1
        return None

def generate_tree(startpath: Path) -> str:
    """Generate a tree representation of the directory structure."""
    tree = []
    startpath = startpath.resolve()

    def add_to_tree(path: Path, prefix: str = ''):
        nonlocal tree
        files = []
        dirs = []

        for item in sorted(path.iterdir()):
            if should_exclude(item, startpath):
                continue
            if item.is_file():
                files.append(item.name)
            elif item.is_dir():
                dirs.append(item)

        for i, file in enumerate(files):
            if i == len(files) - 1 and not dirs:
                tree.append(f"{prefix}└── {file}")
            else:
                tree.append(f"{prefix}├── {file}")

        for i, dir in enumerate(dirs):
            is_last = (i == len(dirs) - 1)
            tree.append(f"{prefix}{'└── ' if is_last else '├── '}{dir.name}/")
            add_to_tree(dir, prefix + ('    ' if is_last else '│   '))

    tree.append(f"{startpath.name}/")
    add_to_tree(startpath)

    # Add the final curved lines
    if len(tree) > 1:
        last_lines = []
        for line in reversed(tree):
            if line.startswith('└── '):
                last_lines.append(line)
            else:
                break
        
        for i, line in enumerate(reversed(last_lines)):
            indent = '    ' * i
            tree[len(tree) - i - 1] = f"{indent}└── {line.split('└── ', 1)[1]}"

    return '\n'.join(tree)

def generate_map_file(tree: str, output_file: Path):
    """Generate a file containing the repository map in the specified format."""
    try:
        content = f"```\n# Repository Map\n\n{tree}\n\nFile: {output_file.name}\n```\n"
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(content)
        logger.info(f"Generated repository map file: {output_file}")
        metrics.map_file_saved = True
        metrics.map_file_location = output_file.resolve()
    except Exception as e:
        logger.error(f"Error generating map file: {str(e)}")
        metrics.errors += 1

def main():
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description="Generate a repository map.")
    parser.add_argument("--update-files", action="store_true", help="Update existing files with the repository map")
    parser.add_argument("--backup", action="store_true", help="Create backups of files before modifying (only applicable with --update-files)")
    parser.add_argument("--output", default="repo_map.md", help="Output file name for the map file (default: repo_map.md)")
    parser.add_argument("--verbose", action="store_true", help="Enable verbose logging")
    parser.add_argument("--force", action="store_true", help="Force update files even if backup fails")
    args = parser.parse_args()

    # Set logging level based on verbose flag
    if args.verbose:
        logger.setLevel(logging.INFO)
    else:
        logger.setLevel(logging.WARNING)

    try:
        current_dir = Path.cwd()

        logger.info("Generating repository tree...")
        tree = generate_tree(current_dir)

        output_file = current_dir / args.output
        generate_map_file(tree, output_file)

        if args.update_files:
            logger.info("Previewing changes...")
            changes = [f for f in current_dir.rglob('*') if f.is_file() and not should_exclude(f, current_dir) and not is_binary_file(f)]
            
            for change in changes:
                print(f"Would update repo map in: {change}")
            
            if not changes:
                logger.info("No files to update. Exiting.")
                return

            proceed = input("Do you want to proceed with applying changes to existing files? (default: yes, or type 'n' for no): ").strip().lower()
            if proceed == '' or proceed.startswith('y'):
                backup_dir = None
                if args.backup:
                    backup = input("Do you want to create backups before modifying files? (default: yes, or type 'n' for no): ").strip().lower()
                    if backup == '' or backup.startswith('y'):
                        backup_dir = current_dir / '.tree_map_backup' / datetime.now().strftime('%Y%m%d_%H%M%S')
                        backup_dir.mkdir(parents=True, exist_ok=True)
                        logger.info(f"Created backup directory: {backup_dir}")

                logger.info("Updating files with new tree map...")
                modified_files = update_files_with_tree(current_dir, tree, backup_dir)

                if modified_files:
                    logger.info(f"Updated {len(modified_files)} files.")
                    
                    if (current_dir / '.git').exists():
                        git_confirm = input("Do you want to commit these changes to git? (default: yes, or type 'n' for no): ").strip().lower()
                        if git_confirm == '' or git_confirm.startswith('y'):
                            git_commit_changes(modified_files)
                else:
                    logger.info("No files were modified.")

                if backup_dir:
                    logger.info(f"Backup of original files is available at: {backup_dir}")
            else:
                logger.info("File updates cancelled. Exiting.")

        metrics.print_summary()

    except Exception as e:
        logger.error(f"An unexpected error occurred: {str(e)}")
        metrics.errors += 1
        metrics.print_summary()

if __name__ == "__main__":
    metrics = Metrics()
    main()