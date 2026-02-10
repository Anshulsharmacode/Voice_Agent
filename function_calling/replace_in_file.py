from typing import Dict
import os
import difflib

def get_replace_in_file_tool() -> Dict:
    return {
        "type": "function",
        "function": {
            "name": "replace_in_file",
            "description": (
                "Replace lines in a file by matching the old content as a block of lines and replacing it with new content. "
                "This operates on code block lines, not on variable or pattern replacements. "
                "Always returns the changes in git diff format. "
                "If the old content block is not found, returns the closest match and a message indicating the old content does not exist."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "file_path": {
                        "type": "string",
                        "description": "Path to the file to modify (absolute or relative to current working directory)"
                    },
                    "old_content": {
                        "type": "string",
                        "description": "The exact old content block (lines) to be replaced in the file"
                    },
                    "new_content": {
                        "type": "string",
                        "description": "New content block (lines) to replace the old content block with"
                    }
                },
                "required": ["file_path", "old_content", "new_content"]
            }
        }
    }
    

async def replace_in_file(
    file_path: str,
    old_content: str,
    new_content: str,
    working_directory: str = None
) -> str:
    """
    Replace a section of a file by matching the old content exactly and replacing it with new content.
    Always returns the changes in git diff format.
    If the old content is not found, returns the closest match and a message indicating the old content does not exist.

    Args:
        file_path: Path to the file to modify (absolute or relative to working_directory)
        old_content: The exact old content to be replaced in the file
        new_content: New content to replace the old content with
        working_directory: Base directory for resolving relative paths (defaults to current working directory)

    Returns:
        Success message with git diff or error message
    """
    try:
        # Determine the working directory to use
        base_dir = working_directory or os.getcwd()
        current_dir = os.getcwd()
        # Only allow operation if we are in the working_directory
        if os.path.abspath(current_dir) != os.path.abspath(base_dir):
            return (
                f"Error: Not in the correct directory. "
                f"First move to {os.path.abspath(base_dir)} and try again."
            )

        # Handle relative paths - convert to absolute path using working_directory
        if not os.path.isabs(file_path):
            base_dir = working_directory or os.getcwd()
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
            original_text = f.read()

        # Try to find the old_content in the file
        idx = original_text.find(old_content)
        if idx == -1:
            # Find the closest match using difflib
            original_lines = original_text.splitlines(keepends=True)
            old_lines = old_content.splitlines(keepends=True)
            # Find the best matching block
            sm = difflib.SequenceMatcher(None, original_text, old_content)
            # Get the best matching block
            best = sm.find_longest_match(0, len(original_text), 0, len(old_content))
            if best.size > 0:
                closest = original_text[best.a:best.a+best.size]
                # Show a few lines of context around the closest match
                context_start = max(0, best.a - 40)
                context_end = min(len(original_text), best.a + best.size + 40)
                closest_context = original_text[context_start:context_end]
                return (
                    "Error: The specified old_content was not found in the file.\n"
                    "Closest match in file (with some context):\n"
                    "------------------\n"
                    f"{closest_context}\n"
                    "------------------\n"
                    "Please provide the exact old content as it appears in the file."
                )
            else:
                return (
                    "Error: The specified old_content was not found in the file, and no similar content was detected.\n"
                    "Please provide the exact old content as it appears in the file."
                )

        # Replace the first occurrence of old_content with new_content
        modified_text = original_text.replace(old_content, new_content, 1)

        # Write the modified content to the file
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(modified_text)

        # Prepare the diff
        original_lines = original_text.splitlines(keepends=True)
        modified_lines = modified_text.splitlines(keepends=True)
        diff = difflib.unified_diff(
            original_lines,
            modified_lines,
            fromfile=f'a/{os.path.basename(file_path)}',
            tofile=f'b/{os.path.basename(file_path)}',
            n=3  # Context lines
        )
        diff_text = ''.join(diff)
        if not diff_text:
            diff_text = "No changes detected (the new content may be identical to the original old content)."

        return f"Successfully modified {file_path}. Changes:\n\n{diff_text}"

    except PermissionError:
        return f"Error: Permission denied when modifying {file_path}"
    except IsADirectoryError:
        return f"Error: {file_path} is a directory"
    except ValueError as e:
        return f"Error: Invalid parameter format: {str(e)}"
    except Exception as e:
        return f"Error modifying file: {str(e)}"
