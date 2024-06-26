# 🗺️ Repository Map Generator

A simple-to-use Python script to generate, maintain, and integrate a visual tree map of your project's directory structure. This tool offers a range of features including repo map insertion into existing files, Git integration, and robust file handling.

![Python Version](https://img.shields.io/badge/python-3.6%2B-blue)
![License](https://img.shields.io/badge/license-MIT-green)

## ❔ Why Use a Repo Map

When utilizing a Language Model (LLM) and working with a larger codebase, including a repository map can improve accuracy of generated code. We manually copy/paste the repo map file or include it as a comment at the top of each code file to provide the LLM with essential context. This can lead to better code comprehension and more precise interactions.

## 👀 Preview

```
# Repository Map

repo_map_generator/
├── misc/
│   └── cat_pictures/
└── secret_plans/
    ├── girl_scout_thin_mints_recipe.md
    ├── world_domination_checklist.md
    └── next_gen_ai/
        ├── TODO.py
        └── skynet_prototype.py

File: repo_map.md
```

## ✨ Features

- 🌳 Generate a tree-like map of your repository
- 📄 Create a standalone Markdown file with the repository map
- 🔄 [Optional] Update relevant files in the repository to add a comment with the current repo map at the top of the file.
- 💾 [Optional] Git integration for automatic commits
- 🔒 [Optional] Backup functionality to preserve original files
- 🎨 Support for various file types with appropriate comment styles
- 🚫 Intelligent file and directory exclusions
- 📏 Long path handling for backups
- 📊 Detailed metrics and execution summary

## 🛠️ Requirements

- Python 3.6+
- Git (optional, for version control integration)

## 🚀 Usage

1. Place the `repo_map_generator.py` file in the root directory of your repository.
2. Run the script with:

```bash
python repo_map_generator.py
```

This will generate a `repo_map.md` file in the current directory.

### Options

| Option | Description |
|--------|-------------|
| `--update-files` | Update existing files with the repository map |
| `--backup` | Create backups before modifying files (use with --update-files) |
| `--output FILENAME` | Specify the output file name (default: repo_map.md) |
| `--verbose` | Enable verbose logging |
| `--force` | Force update files even if backup fails |

Example:

```bash
python repo_map_generator.py --update-files --backup --output my_repo_map.md --verbose
```

## 🔍 How It Works

1. Traverses the directory structure
2. Generates a tree-like representation
3. Creates a Markdown file with the map
4. Optionally updates files with the new map (with user confirmation)
5. Provides options for backing up files before modifications
6. Handles binary files and long paths
7. Offers Git integration for committing changes

## 🔧 Customization

Modify `EXCLUDE_FILES`, `EXCLUDE_DIRS`, and `COMMENT_STYLES` in the script to customize behavior. These comprehensive sets allow for fine-tuned control over which files and directories are included or excluded from the map.

## 🔀 Git Integration

When used in a Git repository, the script offers an option to automatically commit changes:
- After updating files, it prompts to commit changes
- If confirmed, stages modified files and creates a commit
- Commit message: "Update repository map"

This ensures your repository map updates are properly versioned.

## 📊 Metrics

The script now provides a detailed summary of its execution, including:
- Total files processed
- Files modified
- Files skipped
- Backup size
- Errors encountered
- Total execution time

## 🛡️ Safety Features

- Preview changes before applying
- Option to create backups before modifying files
- Binary file detection to avoid corrupting non-text files
- Handling of long file paths for backups

## 👥 Contributing

Contributions are welcome! Please feel free to submit issues or pull requests.

## 📄 License

[MIT License](LICENSE)

---

For questions or issues, please open an issue on the GitHub repository.
