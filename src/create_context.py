import argparse
import ast
import os


def get_directory_tree(directory, include_dirs=None, exclude_dirs=None):
    """Generates a string representation of the directory tree structure with filtering."""
    output = []
    level = 0
    indent = "    "

    def should_include(dir_path):
        if include_dirs is None:
            return True
        return any(
            os.path.abspath(os.path.join(directory, d)) in os.path.abspath(dir_path)
            for d in include_dirs
        )

    def should_exclude(dir_path):
        return any(
            os.path.abspath(os.path.join(directory, d)) in os.path.abspath(dir_path)
            for d in exclude_dirs
        )

    def traverse(dir_path, level):
        items = sorted(os.listdir(dir_path))
        num_items = len(items)
        for i, item in enumerate(items):
            item_path = os.path.join(dir_path, item)

            # Apply directory filtering here
            if os.path.isdir(item_path):
                if exclude_dirs and should_exclude(item_path):
                    continue
                if include_dirs is not None and not should_include(item_path):
                    continue

            is_last = i == num_items - 1
            branch = "└── " if is_last else "├── "
            output.append(indent * level + branch + item)
            if os.path.isdir(item_path):
                traverse(item_path, level + 1)

    # Always include the base directory
    output.append(os.path.basename(directory))
    traverse(directory, 0)
    return "\n".join(output)


def get_file_contents(file_path):
    """Reads the contents of a file."""
    try:
        with open(file_path, "r") as f:
            contents = f.read()
        return contents
    except FileNotFoundError:
        print(f"Error: File not found - {file_path}")
        return ""


def find_related_files(base_file_path, directory):
    """Finds files related to the base file via import statements."""
    related_files = set()
    processed_files = set()
    queue = [base_file_path]

    while queue:
        current_file_path = queue.pop(0)
        if current_file_path in processed_files:
            continue
        processed_files.add(current_file_path)

        try:
            with open(current_file_path, "r") as f:
                tree = ast.parse(f.read())
                for node in ast.walk(tree):
                    if isinstance(node, (ast.Import, ast.ImportFrom)):
                        for alias in node.names:
                            module_name = alias.name
                            # Try to find local files matching the import
                            possible_paths = [
                                os.path.join(
                                    directory, module_name.replace(".", os.sep) + ".py"
                                ),
                                os.path.join(
                                    os.path.dirname(current_file_path),
                                    module_name.split(".")[-1] + ".py",
                                ),
                                (
                                    os.path.join(
                                        directory,
                                        *module_name.split(".")[:-1],
                                        module_name.split(".")[-1] + ".py",
                                    )
                                    if "." in module_name
                                    else None
                                ),
                            ]
                            for path in possible_paths:
                                if (
                                    path
                                    and os.path.exists(path)
                                    and path not in processed_files
                                ):
                                    related_files.add(path)
                                    queue.append(path)
        except (FileNotFoundError, SyntaxError):
            pass  # Ignore if the file doesn't exist or has syntax errors

    return related_files


def make_context_from_dir(
    directory,
    include=(".py",),
    exclude=(),
    recursive=True,
    include_dirs=None,
    exclude_dirs=None,
    related_file=None,
):
    """Processes the directory to generate structure and file contents."""
    output_parts = [
        get_directory_tree(
            directory, include_dirs=include_dirs, exclude_dirs=exclude_dirs
        )
        + "\n\n"
    ]
    python_files = []

    processed_files = set()

    if related_file:
        related_file_path = os.path.join(directory, related_file)
        if os.path.exists(related_file_path):
            related_files = find_related_files(related_file_path, directory)
            for file_path in related_files:
                if file_path not in processed_files:
                    contents = get_file_contents(file_path)
                    python_files.append((file_path, contents))
                    processed_files.add(file_path)
        else:
            print(f"Warning: Related file not found - {related_file_path}")

    def should_include_dir(dir_path):
        if include_dirs:
            return any(
                os.path.abspath(os.path.join(directory, d)) in os.path.abspath(dir_path)
                for d in include_dirs
            )
        return True

    def should_exclude_dir(dir_path):
        if exclude_dirs is None:
            return False  # No exclusions if None is given
            
        default_excludes = {".git", ".github", ".env", ".venv", "venv", "__pycache__", "node_modules"}
        rel_path = os.path.relpath(dir_path, directory)
        path_parts = rel_path.split(os.sep)
        
        # Check if any part of the path matches default excludes
        if exclude_dirs != []:  # Only check default excludes if exclude_dirs is not an empty list
            if any(part in default_excludes for part in path_parts):
                return True
            
        # Check user-specified excludes
        return any(
            os.path.abspath(os.path.join(directory, d)) in os.path.abspath(dir_path)
            for d in exclude_dirs
        )

    for root, dirs, files in os.walk(directory):
        # Modify dirs in-place to control recursion
        if not recursive:
            dirs[:] = []  # Don't recurse further

        if not should_include_dir(root) or should_exclude_dir(root):
            dirs[:] = []  # Skip this directory and its subdirectories
            continue

        for filename in files:
            if any(filename.endswith(ext) for ext in include) and not any(
                filename.endswith(ext) for ext in exclude
            ):
                file_path = os.path.join(root, filename)
                if file_path not in processed_files:
                    contents = get_file_contents(file_path)
                    python_files.append((file_path, contents))
                    processed_files.add(file_path)

    for file_path, contents in sorted(python_files):
        output_parts.append(f"File: {file_path}\n\nContents:\n{contents}\n\n")

    return "".join(output_parts)

