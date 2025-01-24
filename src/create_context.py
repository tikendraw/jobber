import argparse
import ast
import os
from pathlib import Path
from typing import Iterator, List, Optional, Set, Tuple


def get_directory_tree(
    directory: Path,
    include_dirs: Optional[List[str]] = None,
    exclude_dirs: Optional[List[str]] = None
) -> str:
    """Generates a string representation of the directory tree structure with filtering."""
    output: List[str] = []
    level = 0
    indent = "    "

    def should_include(dir_path: Path) -> bool:
        if include_dirs is None:
            return True
        return any(
            Path(directory / d) in dir_path.resolve().parents
            for d in include_dirs
        )

    def should_exclude(dir_path: Path) -> bool:
        return any(
            Path(directory / d) in dir_path.resolve().parents
            for d in exclude_dirs
        )

    def traverse(dir_path: Path, level: int) -> None:
        items = sorted(os.listdir(dir_path))
        num_items = len(items)
        for i, item in enumerate(items):
            item_path = dir_path / item

            # Apply directory filtering here
            if item_path.is_dir():
                if exclude_dirs and should_exclude(item_path):
                    continue
                if include_dirs is not None and not should_include(item_path):
                    continue

            is_last = i == num_items - 1
            branch = "└── " if is_last else "├── "
            output.append(indent * level + branch + item)
            if item_path.is_dir():
                traverse(item_path, level + 1)

    # Always include the base directory
    output.append(directory.name)
    traverse(directory, 0)
    return "\n".join(output)


def get_file_contents(file_path: Path) -> str:
    """Reads the contents of a file."""
    try:
        return file_path.read_text()
    except FileNotFoundError:
        print(f"Error: File not found - {file_path}")
        return ""


def find_related_files(base_file_path: Path, directory: Path) -> Set[Path]:
    """Finds files related to the base file via import statements."""
    related_files: Set[Path] = set()
    processed_files: Set[Path] = set()
    queue: List[Path] = [base_file_path]

    while queue:
        current_file_path = queue.pop(0)
        if current_file_path in processed_files:
            continue
        processed_files.add(current_file_path)

        try:
            tree = ast.parse(current_file_path.read_text())
            for node in ast.walk(tree):
                if isinstance(node, (ast.Import, ast.ImportFrom)):
                    for alias in node.names:
                        module_name = alias.name
                        # Try to find local files matching the import
                        possible_paths = [
                            directory / f"{module_name.replace('.', '/')}.py",
                            current_file_path.parent / f"{module_name.split('.')[-1]}.py",
                            (
                                directory.joinpath(*module_name.split('.')[:-1]) / f"{module_name.split('.')[-1]}.py"
                                if '.' in module_name
                                else None
                            ),
                        ]
                        for path in possible_paths:
                            if (
                                path
                                and path.exists()
                                and path not in processed_files
                            ):
                                related_files.add(path)
                                queue.append(path)
        except (FileNotFoundError, SyntaxError):
            pass  # Ignore if the file doesn't exist or has syntax errors

    return related_files


def make_context_from_dir(
    directory: Path,
    include: Tuple[str, ...] = (".py",'.md'),
    exclude: Tuple[str, ...] = ('.ipynb', 'json', '.pkl', 'txt', '.pdf', '.csv'),
    recursive: bool = True,
    include_dirs: Optional[List[str]] = None,
    exclude_dirs: Optional[List[str]] = ['.venv', '.git', '.github', 'venv'],
    related_file: Optional[str] = None,
) -> str:
    """Processes the directory to generate structure and file contents."""
    if not directory.exists():
        return "Error: Directory does not exist"

    tree_structure = get_directory_tree(
        directory, include_dirs=include_dirs, exclude_dirs=exclude_dirs
    )
    output_parts: List[str] = [tree_structure + "\n\n"]
    matched_files: List[Tuple[Path, str]] = []
    processed_files: Set[Path] = set()

    if related_file:
        related_file_path = directory / related_file
        if related_file_path.exists():
            related_files = find_related_files(related_file_path, directory)
            for file_path in related_files:
                if file_path not in processed_files:
                    contents = get_file_contents(file_path)
                    matched_files.append((file_path, contents))
                    processed_files.add(file_path)
        else:
            print(f"Warning: Related file not found - {related_file_path}")

    def should_include_dir(dir_path: Path) -> bool:
        if include_dirs:
            return any(
                Path(directory / d) in dir_path.resolve().parents
                for d in include_dirs
            )
        return True

    def should_exclude_dir(dir_path: Path) -> bool:
        if exclude_dirs is None:
            return False  # No exclusions if None is given
            
        default_excludes = {".git", ".github", ".env", ".venv", "venv", "__pycache__", "node_modules"}
        rel_path = dir_path.relative_to(directory)
        path_parts = rel_path.parts
        
        # Check if any part of the path matches default excludes
        if exclude_dirs != []:  # Only check default excludes if exclude_dirs is not an empty list
            if any(part in default_excludes for part in path_parts):
                return True
            
        # Check user-specified excludes
        return any(
            Path(directory / d) in dir_path.resolve().parents
            for d in exclude_dirs
        )

    for root, dirs, files in os.walk(directory):
        root_path = Path(root)
        # Modify dirs in-place to control recursion
        if not recursive:
            dirs[:] = []  # Don't recurse further

        if not should_include_dir(root_path) or should_exclude_dir(root_path):
            dirs[:] = []  # Skip this directory and its subdirectories
            continue

        for filename in files:
            if any(filename.endswith(ext) for ext in include) and not any(
                filename.endswith(ext) for ext in exclude
            ):
                file_path = root_path / filename
                if file_path not in processed_files:
                    contents = get_file_contents(file_path)
                    matched_files.append((file_path, contents))
                    processed_files.add(file_path)

    if not matched_files:
        return f"Directory structure:\n{tree_structure}\n\nNo matching files found in the directory based on the given criteria."

    for file_path, contents in sorted(matched_files):
        output_parts.append(f"File: {file_path}\n\nContents:\n{contents}\n\n")

    return "".join(output_parts)



if __name__=='__main__':
    a = make_context_from_dir(
        Path('/home/t/atest/scrappa/user_info/github_repos/groq-on/')
    )
    
    b= Path('new_structure.txt').write_text(a)