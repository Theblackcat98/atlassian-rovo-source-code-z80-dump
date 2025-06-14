"""Utilities for handling file types and languages."""

from pathlib import Path
from typing import Tuple

# Special cases for files without extensions
SPECIAL_FILES = {
    "dockerfile": "dockerfile",
    "makefile": "makefile",
    "jenkinsfile": "jenkinsfile",
    "vagrantfile": "ruby",
    "brewfile": "ruby",
}

# Map of file extensions to languages
EXTENSION_LANGUAGES = {
    "py": "python",
    "js": "javascript",
    "ts": "typescript",
    "jsx": "javascript",
    "tsx": "typescript",
    "java": "java",
    "cpp": "cpp",
    "c": "c",
    "cs": "csharp",
    "go": "go",
    "rs": "rust",
    "rb": "ruby",
    "php": "php",
    "sh": "shell",
    "bash": "shell",
    "zsh": "shell",
    "fish": "shell",
    "yaml": "yaml",
    "yml": "yaml",
    "json": "json",
    "md": "markdown",
    "html": "html",
    "css": "css",
    "scss": "scss",
    "sql": "sql",
    "tf": "terraform",
    "tfvars": "terraform",
    "hcl": "hcl",
}


def get_file_type_and_language(file_path: str) -> Tuple[str, str]:
    """
    Get file type and language from file path.

    Args:
        file_path: Path to the file

    Returns:
        Tuple of (file_type, language)
        - file_type: Extension without dot or special case name
        - language: Programming language or text type
    """
    if not file_path:
        return "unknown", "unknown"

    # Convert to Path for easier handling
    path = Path(file_path)

    # Handle special cases (files without extensions)
    name_lower = path.name.lower()
    if name_lower in SPECIAL_FILES:
        return name_lower, SPECIAL_FILES[name_lower]

    # Get extension
    suffix = path.suffix
    if not suffix:
        return "no_extension", "unknown"

    # Remove dot and convert to lowercase
    ext = suffix[1:].lower()

    # Get language from extension
    language = EXTENSION_LANGUAGES.get(ext, "unknown")

    return ext, language
