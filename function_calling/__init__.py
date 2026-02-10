import os
import webbrowser
import urllib.parse
from typing import Dict, Optional, List
from logs import logger

if 'DISPLAY' not in os.environ or os.environ['DISPLAY'] == ':0':
    # Check if :1 or :2 is available
    for display in [':1', ':2']:
        socket_path = f"/tmp/.X11-unix/X{display[1]}"
        if os.path.exists(socket_path):
            os.environ['DISPLAY'] = display
            logger.system(f"Set DISPLAY to {display} (working display)")
            break

from .message import get_message_tool, generic_response
from .finish_task import get_finish_tool
from .calculator import calculate, get_calculator_tool
from .get_weather import get_weather_info, get_weather_tool
from .web_search import search_web, get_web_search_tool
from .webpage_content import get_webpage_content, get_webpage_content_tool
from .plan import get_plan_tool, get_task_tracker_tool, get_task_is_done_tool, create_plan, track_task, task_is_done
from .file_read import get_file_read_tool, read_file
from .write_to_file import get_file_write_tool, write_file
from .replace_in_file import get_replace_in_file_tool, replace_in_file
from .insert_in_file import get_insert_in_file_tool, insert_in_file

from .execute_command import execute_command
from .execute_command import get_execute_command_tool
from .image_analysis import analyze_image, get_image_analysis_tool
from .open_browser import open_browser, get_open_browser_tool


# Try to import UI automation tools with error handling
UI_AUTOMATION_AVAILABLE = False
try:
    from .navigate_ui import (
        take_screenshot, get_screenshot_tool,
        get_window_list, get_window_list_tool,
        focus_window, get_focus_window_tool,
        click_at_position, get_click_tool,
        type_text, get_type_text_tool,
        press_key, get_press_key_tool,
        copy_to_clipboard, get_copy_to_clipboard_tool,
        paste_from_clipboard, get_paste_from_clipboard_tool,
        get_screen_info, get_screen_info_tool
    )
    UI_AUTOMATION_AVAILABLE = True
    logger.system("UI automation tools loaded successfully")
except Exception as e:
    logger.warning(f"UI automation tools not available: {str(e)}")
    logger.warning("UI automation features will be disabled")
    
    raise Exception("UI automation not available - no display server detected")


# Dictionary of all tool executors
TOOL_EXECUTORS = {
    "calculate": calculate,
    "get_weather_info": get_weather_info,
    "search_web": search_web,
    "get_webpage_content": get_webpage_content,
    "generic_response": generic_response,
    "create_plan": create_plan,
    "task_is_done": task_is_done,
    "track_task": track_task,
    "read_file": read_file,
    "write_file": write_file,
    "replace_in_file": replace_in_file,
    "insert_in_file": insert_in_file,
    "execute_command": execute_command,
    "analyze_image": analyze_image,
    "open_browser": open_browser,
    # UI Automation tools (will be dummy functions if not available)
    "take_screenshot": take_screenshot,
    "get_window_list": get_window_list,
    "focus_window": focus_window,
    "click_at_position": click_at_position,
    "type_text": type_text,
    "press_key": press_key,
    "copy_to_clipboard": copy_to_clipboard,
    "paste_from_clipboard": paste_from_clipboard,
    "get_screen_info": get_screen_info
}

# Dictionary of all available tools and their definitions
AVAILABLE_TOOLS = {
    "calculate": get_calculator_tool(),
    "get_weather_info": get_weather_tool(),
    "web_search": get_web_search_tool(),
    "webpage_content": get_webpage_content_tool(),
    "finish": get_finish_tool(),
    "generic_response": get_message_tool(),
    "create_plan": get_plan_tool(),
    "task_is_done": get_task_is_done_tool(),
    "track_task": get_task_tracker_tool(),
    "read_file": get_file_read_tool(),
    "write_file": get_file_write_tool(),
    "replace_in_file": get_replace_in_file_tool(),
    "insert_in_file": get_insert_in_file_tool(),
    "execute_command": get_execute_command_tool(),
    "analyze_image": get_image_analysis_tool(),
    "open_browser": get_open_browser_tool(),
    # UI Automation tools (will be dummy tools if not available)
    "take_screenshot": get_screenshot_tool(),
    "get_window_list": get_window_list_tool(),
    "focus_window": get_focus_window_tool(),
    "click_at_position": get_click_tool(),
    "type_text": get_type_text_tool(),
    "press_key": get_press_key_tool(),
    "copy_to_clipboard": get_copy_to_clipboard_tool(),
    "paste_from_clipboard": get_paste_from_clipboard_tool(),
    "get_screen_info": get_screen_info_tool()
}

def get_tools(tool_names: List[str]) -> List[Dict]:
    """Get a list of tool definitions based on their names"""
    return [AVAILABLE_TOOLS[name] for name in tool_names if name in AVAILABLE_TOOLS]

async def execute_tool(tool_name: str, **kwargs):
    """Execute a tool by name with given arguments"""
    if tool_name not in TOOL_EXECUTORS:
        raise ValueError(f"Unknown tool: {tool_name}")
    
    try:
        executor = TOOL_EXECUTORS[tool_name]
        return await executor(**kwargs)
    except Exception as e:
        raise ValueError(f"Error executing {tool_name}: {str(e)}")

# Export everything needed
__all__ = [
    'get_tools',
    'execute_tool',
    'AVAILABLE_TOOLS',
    'TOOL_EXECUTORS',
    'UI_AUTOMATION_AVAILABLE',
    # Export individual tools if needed
    'get_weather_tool',
    'get_weather_info',
    'get_calculator_tool',
    'calculate',
    'get_web_search_tool',
    'search_web',
    'get_webpage_content_tool',
    'get_webpage_content',
    'get_finish_tool',
    'get_message_tool',
    'generic_response',
    'get_plan_tool',
    'create_plan',
    'get_task_is_done_tool',
    'task_is_done',
    'get_task_tracker_tool',
    'track_task',
    'get_file_read_tool',
    'read_file',
    'get_file_write_tool',
    'write_file',
    'get_replace_in_file_tool',
    'replace_in_file',
    'get_insert_in_file_tool',
    'insert_in_file',
    'execute_command',
    'get_execute_command_tool',
    'analyze_image',
    'get_image_analysis_tool',
    'open_browser',
    'get_open_browser_tool',
    # UI Automation exports (will be dummy functions if not available)
    'take_screenshot',
    'get_screenshot_tool',
    'get_window_list',
    'get_window_list_tool',
    'focus_window',
    'get_focus_window_tool',
    'click_at_position',
    'get_click_tool',
    'type_text',
    'get_type_text_tool',
    'press_key',
    'get_press_key_tool',
    'copy_to_clipboard',
    'get_copy_to_clipboard_tool',
    'paste_from_clipboard',
    'get_paste_from_clipboard_tool',
    'get_screen_info',
    'get_screen_info_tool'
]
