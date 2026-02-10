import subprocess
import asyncio
import re
from typing import Dict, Optional, List

def get_execute_command_tool() -> Dict:
    return {
        "type": "function",
        "function": {
            "name": "execute_command",
            "description": "Execute a shell command and return the output (with security restrictions)",
            "parameters": {
                "type": "object",
                "properties": {
                    "command": {
                        "type": "string",
                        "description": "The shell command to execute (restricted to safe commands only)"
                    }
                },
                "required": ["command"]
            }
        }
    }

def is_command_allowed(command: str) -> tuple[bool, str]:
    """
    Check if a command is allowed to be executed
    
    Args:
        command: The command to check
        
    Returns:
        Tuple of (is_allowed, reason)
    """
    # Convert to lowercase for case-insensitive matching
    cmd_lower = command.lower().strip()
    
    # List of dangerous commands and patterns
    dangerous_patterns = [
        # Sudo and root commands
        r'\bsudo\b',
        r'\bsu\b',
        r'\bdoas\b',
        r'\bpkexec\b',
        r'\bgksudo\b',
        r'\bkdesudo\b',
        
        # Destructive file operations
        r'\brm\b',
        r'\brmdir\b',
        r'\bdel\b',
        r'\bdelete\b',
        r'\bformat\b',
        r'\bwipe\b',
        r'\bdd\b.*\bof=/',
        r'\bshred\b',
        r'\bunlink\b',
        
        # Dangerous file copy/move operations
        r'\bcp\b.*\b/\s*$',  # cp to root
        r'\bcp\b.*\b~/',      # cp to home
        r'\bcp\b.*\b/home/',  # cp to /home
        r'\bmv\b.*\b/\s*$',   # mv to root
        r'\bmv\b.*\b~/',      # mv to home
        r'\bmv\b.*\b/home/',  # mv to /home
        r'\bscp\b',
        r'\brsync\b.*\b--delete\b',
        r'\btar\b.*\b--delete\b',
        
        # System modification commands
        r'\bchmod\b.*\b777\b',
        r'\bchown\b.*\broot\b',
        r'\bmount\b',
        r'\bumount\b',
        r'\binit\b',
        r'\bshutdown\b',
        r'\breboot\b',
        r'\bhalt\b',
        r'\bpoweroff\b',
        
        # Network and security
        r'\biptables\b',
        r'\bip\b.*\blink\b',
        r'\broute\b',
        r'\bpasswd\b',
        r'\buseradd\b',
        r'\buserdel\b',
        r'\bgroupadd\b',
        r'\bgroupdel\b',
        
        # Package management (can be dangerous)
        r'\bapt-get\b.*\bremove\b',
        r'\bapt-get\b.*\bpurge\b',
        r'\byum\b.*\bremove\b',
        r'\bdnf\b.*\bremove\b',
        r'\bpacman\b.*\b-R\b',
        r'\bzypper\b.*\bremove\b',
        
        # Process management
        r'\bkill\b.*\b-9\b',
        r'\bkillall\b',
        r'\bpkill\b',
        
        # Shell and execution with dangerous commands
        r'\bbash\b.*\b-c\b.*\brm\b',
        r'\bsh\b.*\b-c\b.*\brm\b',
        r'\bexec\b.*\brm\b',
        
        # Dangerous redirects
        r'>.*/dev/',
        r'>>.*/dev/',
        r'2>.*/dev/',
        r'2>>.*/dev/',
        
        # Pipeline with dangerous commands
        r'\|.*\brm\b',
        r'\|.*\bsudo\b',
        r'\|.*\bsu\b',
        
        # Command substitution with dangerous commands
        r'\$\(.*\brm\b',
        r'\$\(.*\bsudo\b',
        r'\$\(.*\bsu\b',
    ]
    
    # Check for dangerous patterns
    for pattern in dangerous_patterns:
        if re.search(pattern, cmd_lower):
            return False, f"Command blocked: contains dangerous pattern '{pattern}'"
    
    # Check for dangerous cd commands (only block dangerous paths)
    if 'cd' in cmd_lower:
        dangerous_cd_paths = ['~', '/home/', '/ ']
        if any(path in command for path in dangerous_cd_paths):
            return False, "Command blocked: cd to home directory or root not allowed"
    
    # Check for dangerous chaining (only block when combined with dangerous commands)
    if ';' in command or '&&' in command or '||' in command:
        # Allow chaining but check if it contains dangerous commands
        commands = re.split(r'[;&&||]+', command)
        for cmd in commands:
            cmd = cmd.strip()
            if any(dangerous in cmd.lower() for dangerous in ['rm', 'sudo', 'su', 'dd', 'shred']):
                return False, "Command blocked: chaining with dangerous commands not allowed"
    
    # Check for command substitution with dangerous commands
    if '$(' in command or '`' in command:
        if any(dangerous in command.lower() for dangerous in ['rm', 'sudo', 'su', 'dd', 'shred']):
            return False, "Command blocked: command substitution with dangerous commands not allowed"
    
    # Check for dangerous redirects
    if '>' in command and ('/dev/' in command or '>/dev/' in command):
        return False, "Command blocked: dangerous redirects not allowed"
    
    # Check for shell execution with dangerous commands
    if command.strip().startswith(('bash -c', 'sh -c', 'zsh -c', 'ksh -c')):
        if any(dangerous in command.lower() for dangerous in ['rm', 'sudo', 'su', 'dd', 'shred']):
            return False, "Command blocked: shell execution with dangerous commands not allowed"
    
    return True, "Command allowed"

async def execute_command(
    command: str, 
    working_directory: Optional[str] = None, 
    timeout: float = 30.0
) -> str:
    """
    Execute a shell command and return the output (with security restrictions)
    
    Args:
        command: The shell command to execute
        working_directory: Optional working directory to run the command in
        timeout: Timeout in seconds for command execution
    
    Returns:
        Command output as string (both stdout and stderr)
    """
    # Security check
    is_allowed, reason = is_command_allowed(command)
    if not is_allowed:
        return f"SECURITY BLOCKED: {reason}\nCommand: {command}"
    
    try:
        # Create the subprocess with additional security
        process = await asyncio.create_subprocess_shell(
            command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=working_directory,
            # Additional security: don't inherit environment variables that might contain sensitive data
            env={'PATH': '/usr/local/bin:/usr/bin:/bin:/usr/local/sbin:/usr/sbin:/sbin'}
        )
        
        # Wait for completion with timeout
        stdout, stderr = await asyncio.wait_for(
            process.communicate(), 
            timeout=timeout
        )
        
        # Decode output
        stdout_text = stdout.decode('utf-8') if stdout else ""
        stderr_text = stderr.decode('utf-8') if stderr else ""
        
        # Combine output
        output = ""
        if stdout_text:
            output += f"STDOUT:\n{stdout_text}"
        if stderr_text:
            output += f"\nSTDERR:\n{stderr_text}"
        
        # Add return code info
        output += f"\nReturn code: {process.returncode}"
        
        return output
        
    except asyncio.TimeoutError:
        return f"Command timed out after {timeout} seconds"
    except Exception as e:
        return f"Error executing command: {str(e)}"