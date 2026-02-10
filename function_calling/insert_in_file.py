from typing import Dict
import os

def get_insert_in_file_tool() -> Dict:
    return {
        "type": "function",
        "function": {
            "name": "insert_in_file",
            "description": (
                "Insert content at a specific line number in a file. "
                "The content after the insertion point will be pushed down. "
                "Line numbers are 1-indexed (first line is line 1). "
                "Only allows inserting into files in the current working directory."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "file_path": {
                        "type": "string",
                        "description": "Path to the file to modify (absolute or relative to current working directory)"
                    },
                    "line_number": {
                        "type": "integer",
                        "description": "Line number where to insert the content (1-indexed)"
                    },
                    "content": {
                        "type": "string",
                        "description": "Content to insert at the specified line number"
                    }
                },
                "required": ["file_path", "line_number", "content"]
            }
        }
    }

async def insert_in_file(
    file_path: str,
    line_number: int,
    content: str,
    working_directory: str = None
) -> str:
    """
    Insert content at a specific line number in a file.
    The content after the insertion point will be pushed down.
    Line numbers are 1-indexed (first line is line 1).
    0 means the first line (same as 1). -1 means the last line (insert after the last line).
    Only allows inserting into files in the current working directory.

    Args:
        file_path: Path to the file to modify (absolute or relative to working_directory)
        line_number: Line number where to insert the content (1-indexed, 0=first line, -1=last line)
        content: Content to insert at the specified line number
        working_directory: Base directory for resolving relative paths (defaults to current working directory)

    Returns:
        Success message or error message
    """
    try:
        # Convert parameters to correct types if they're strings
        if isinstance(line_number, str):
            line_number = int(line_number)

        # Determine the working directory to use
        base_dir = working_directory or os.getcwd()
        current_dir = os.getcwd()
        abs_base_dir = os.path.abspath(base_dir)
        abs_current_dir = os.path.abspath(current_dir)

        # Only allow operation if we are in the working directory
        if abs_current_dir != abs_base_dir:
            return f"Error: Not in the correct directory. First move to {abs_base_dir}"

        # Handle relative paths - convert to absolute path using working_directory
        if not os.path.isabs(file_path):
            file_path = os.path.join(base_dir, file_path)
            file_path = os.path.abspath(file_path)

        # Check if file exists
        if not os.path.exists(file_path):
            return f"Error: File not found: {file_path}"

        # Check if it's a directory
        if os.path.isdir(file_path):
            return f"Error: {file_path} is a directory, not a file"

        # Read the original file
        with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
            lines = f.readlines()

        # Handle line_number: 0 means first line, -1 means last line (append after last line)
        if line_number == 0:
            insert_index = 0
            display_line = 1
        elif line_number == -1:
            insert_index = len(lines)
            display_line = len(lines) + 1
        elif line_number < -1:
            return f"Error: Line number must be >= 0 or -1 for last line, got {line_number}"
        else:
            # Validate line number
            if line_number > len(lines) + 1:
                return f"Error: Line number {line_number} is beyond the end of the file (file has {len(lines)} lines)"
            insert_index = line_number - 1
            display_line = line_number

        # Split content into lines and ensure proper line endings
        content_lines = content.splitlines(keepends=True)
        if content_lines and not content_lines[-1].endswith('\n'):
            content_lines[-1] += '\n'

        # Insert the content
        lines[insert_index:insert_index] = content_lines

        # Write the modified content back to the file
        with open(file_path, 'w', encoding='utf-8') as f:
            f.writelines(lines)

        # Calculate statistics
        inserted_lines = len(content_lines)
        total_lines = len(lines)

        return (
            f"Successfully inserted {inserted_lines} lines at line {display_line} in {file_path}. "
            f"File now has {total_lines} total lines."
        )

    except ValueError as e:
        return f"Error: Invalid parameter format: {str(e)}"
    except PermissionError:
        return f"Error: Permission denied when modifying {file_path}"
    except Exception as e:
        return f"Error inserting into file: {str(e)}"