from typing import Dict, Optional
import os
import asyncio

def get_file_read_tool() -> Dict:
    return {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": "Read the contents of a file from the file system",
            "parameters": {
                "type": "object",
                "properties": {
                    "file_path": {
                        "type": "string",
                        "description": "Path to the file to read (absolute or relative to current working directory)"
                    },
                    "max_lines": {
                        "type": "integer",
                        "description": "Maximum number of lines to read from the file",
                        "default": 100
                    },
                    "start_line": {
                        "type": "integer",
                        "description": "Line number to start reading from (0-indexed)",
                        "default": 0
                    }
                },
                "required": ["file_path"]
            }
        }
    }

async def read_file(
    file_path: str, 
    max_lines: Optional[int] = 100, 
    start_line: Optional[int] = 0,
    working_directory: str = None
) -> str:
    """
    Read and return the contents of a file
    
    Args:
        file_path: Path to the file to read (absolute or relative to working_directory)
        max_lines: Maximum number of lines to read from the file (default: 100)
        start_line: Line number to start reading from, 0-indexed (default: 0)
        working_directory: Base directory for resolving relative paths (defaults to current working directory)
    
    Returns:
        String containing the file contents or error message
    """
    try:
        # Convert parameters to correct types if they're strings
        if isinstance(max_lines, str):
            max_lines = int(max_lines)
        if isinstance(start_line, str):
            start_line = int(start_line)
            
        # Validate parameters
        max_lines = max(1, min(max_lines, 1000))  # Cap maximum lines
        start_line = max(0, start_line)  # Ensure start_line is non-negative

        # Determine the working directory to use
        base_dir = working_directory or os.getcwd()
        current_dir = os.getcwd()
        abs_base_dir = os.path.abspath(base_dir)
        abs_current_dir = os.path.abspath(current_dir)

        # Only allow reading if in the correct working directory
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
        
        # Read the file
        with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
            # Skip lines if needed
            for i in range(start_line):
                if not f.readline():
                    return f"Error: Start line {start_line} is beyond the end of the file"
            
            # Read requested number of lines
            lines = []
            for i in range(max_lines):
                line = f.readline()
                if not line:  # End of file
                    break
                lines.append(line)
            
            if not lines:
                if start_line > 0:
                    return f"No content found starting from line {start_line}"
                return "The file is empty"
            
            # Always show line numbers
            line_numbered_content = []
            line_width = len(str(start_line + len(lines)))
            
            for i, line in enumerate(lines, start_line + 1):
                # Remove trailing newline for clean formatting
                if line.endswith('\n'):
                    formatted_line = line[:-1]
                else:
                    formatted_line = line
                    
                line_numbered_content.append(
                    f"{i:{line_width}d} | {formatted_line}"
                )
            
            file_content = '\n'.join(line_numbered_content)
            
            # Add information about file size if we didn't read the whole file
            total_lines = sum(1 for _ in open(file_path, 'r', encoding='utf-8', errors='replace'))
            if total_lines > start_line + len(lines):
                remaining = total_lines - (start_line + len(lines))
                file_content += f"\n\n[File continues for {remaining} more lines]"
            
            return file_content
    
    except ValueError as e:
        return f"Error: Invalid parameter format: {str(e)}"
    except Exception as e:
        return f"Error reading file: {str(e)}"