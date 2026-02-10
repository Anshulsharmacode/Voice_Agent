from typing import Dict
import os
import asyncio

def get_file_write_tool() -> Dict:
    return {
        "type": "function",
        "function": {
            "name": "write_file",
            "description": (
                "Write content to a file, creating it if it doesn't exist or overwriting it if it does. "
                "Only allows writing to files in the current working directory. "
                "If not in the correct directory, you must move to the working directory first."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "file_path": {
                        "type": "string",
                        "description": "Path to the file to write (absolute or relative to current working directory)"
                    },
                    "content": {
                        "type": "string",
                        "description": "Content to write to the file"
                    }
                },
                "required": ["file_path", "content"]
            }
        }
    }

async def write_file(file_path: str, content: str, working_directory: str = None) -> str:
    """
    Write content to a file, creating it if it doesn't exist or overwriting it if it does.
    Only allows writing to files in the current working directory.
    If not in the correct directory, you must move to the working directory first.

    Args:
        file_path: Path to the file to write (absolute or relative to working_directory)
        content: Content to write to the file
        working_directory: Base directory for resolving relative paths (defaults to current working directory)

    Returns:
        Success message or error message
    """
    try:
        # Determine the working directory
        base_dir = working_directory or os.getcwd()
        base_dir = os.path.abspath(base_dir)

        # Handle relative paths - convert to absolute path using working_directory
        if not os.path.isabs(file_path):
            file_path_abs = os.path.abspath(os.path.join(base_dir, file_path))
        else:
            file_path_abs = os.path.abspath(file_path)

        # Only allow writing to files under the working directory
        # (must be inside base_dir, not just /home/yogendramanawat/)
        if not (file_path_abs == base_dir or file_path_abs.startswith(base_dir + os.sep)):
            return (
                f"Error: Not in the correct directory. "
                f"First move to the working directory: {base_dir}"
            )

        # Create parent directories if they do not exist
        directory = os.path.dirname(file_path_abs)
        if directory and not os.path.exists(directory):
            os.makedirs(directory, exist_ok=True)

        # Check if the path points to a directory
        if os.path.exists(file_path_abs) and os.path.isdir(file_path_abs):
            return f"Error: Cannot write to {file_path_abs} because it is a directory"

        # Write to the file
        with open(file_path_abs, 'w', encoding='utf-8') as f:
            f.write(content)

        file_size = len(content)
        line_count = content.count('\n') + 1 if content else 0

        return f"Successfully wrote {file_size} bytes ({line_count} lines) to {file_path_abs}"

    except PermissionError:
        return f"Error: Permission denied when writing to {file_path}"
    except IsADirectoryError:
        return f"Error: {file_path} is a directory"
    except FileNotFoundError:
        return f"Error: Parent directory does not exist for {file_path}"
    except Exception as e:
        return f"Error writing to file: {str(e)}"
