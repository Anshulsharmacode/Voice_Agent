import os
import time
import subprocess
import json
import base64
from typing import Dict, Optional, Tuple, List
from PIL import Image
import io
from logs import logger

# Try to import UI automation libraries
try:
    import pyautogui
    PYAUTOGUI_AVAILABLE = True
    logger.system("pyautogui available for UI automation")
except ImportError:
    PYAUTOGUI_AVAILABLE = False
    logger.warning("pyautogui not available. Install with: pip install pyautogui")

try:
    import mss
    MSS_AVAILABLE = True
    logger.system("mss available for screenshots")
except ImportError:
    MSS_AVAILABLE = False
    logger.warning("mss not available. Install with: pip install mss")

class UIAutomation:
    """Ubuntu UI Automation class with screen capture, window management, and input automation"""
    
    def __init__(self):
        self.screenshot_dir = "screenshots"
        os.makedirs(self.screenshot_dir, exist_ok=True)
        
        # Configure pyautogui if available
        if PYAUTOGUI_AVAILABLE:
            try:
                import pyautogui
                pyautogui.FAILSAFE = True  # Move mouse to corner to stop
                pyautogui.PAUSE = 0.1  # Small delay between actions
            except Exception as e:
                logger.warning(f"Failed to configure pyautogui: {str(e)}")
    
    def _get_monitor_info(self) -> List[Dict]:
        """Get information about available monitors"""
        try:
            result = subprocess.run(['xrandr'], capture_output=True, text=True)
            if result.returncode == 0:
                monitors = []
                for line in result.stdout.split('\n'):
                    if ' connected ' in line:
                        parts = line.split()
                        monitor_name = parts[0]
                        resolution = None
                        position = None
                        
                        # Parse the line to find resolution and position
                        for part in parts:
                            if 'x' in part and part[0].isdigit():
                                if '+' in part:
                                    position = part
                                    resolution = part.split('+')[0]
                                else:
                                    resolution = part
                        
                        monitors.append({
                            'name': monitor_name,
                            'resolution': resolution,
                            'position': position
                        })
                
                return monitors
            else:
                return []
        except Exception as e:
            logger.warning(f"Error getting monitor info: {str(e)}")
            return []
    
    def take_screenshot(self, filename: str = None, monitor: str = None) -> str:
        """Take a screenshot and return the file path
        
        Args:
            filename: Optional filename for the screenshot
            monitor: Monitor to capture ('primary', 'secondary', or monitor name like 'HDMI-1')
        """
        # Ensure filename has .png extension
        if filename is None:
            timestamp = int(time.time())
            monitor_suffix = f"_{monitor}" if monitor else ""
            filename = f"screenshot{monitor_suffix}_{timestamp}.png"
        elif not filename.lower().endswith('.png'):
            filename = filename + '.png'
        
        filepath = os.path.join(self.screenshot_dir, filename)
        
        # Get monitor information
        monitors = self._get_monitor_info()
        
        # If no monitor specified, default to HDMI (secondary) monitor
        if monitor is None:
            # Find HDMI monitor (secondary)
            for m in monitors:
                if 'HDMI' in m['name'].upper() or 'secondary' in m['name'].lower():
                    monitor = m['name']
                    logger.system(f"Defaulting to HDMI monitor: {monitor}")
                    break
            else:
                # If no HDMI found, use the second monitor if available
                if len(monitors) > 1:
                    # Skip the primary monitor (marked with *)
                    secondary_monitors = [m for m in monitors if '*' not in m['name']]
                    if secondary_monitors:
                        monitor = secondary_monitors[0]['name']
                        logger.system(f"Defaulting to secondary monitor: {monitor}")
        
        if monitor and monitor != 'all':
            # Find the specific monitor
            target_monitor = None
            for m in monitors:
                if m['name'] == monitor or (monitor == "primary" and '*' in m['name']):
                    target_monitor = m
                    break
            
            if target_monitor and target_monitor['position']:
                # Parse position and resolution
                position_parts = target_monitor['position'].split('+')
                resolution_part = position_parts[0]
                x = int(position_parts[1])
                y = int(position_parts[2])
                width, height = map(int, resolution_part.split('x'))
                
                logger.system(f"Capturing monitor {target_monitor['name']}: {width}x{height} at {x},{y}")
                
                # Method: Take full screenshot and crop
                timestamp = int(time.time())
                temp_file = os.path.join(self.screenshot_dir, f"temp_{timestamp}.png")
                
                # Take full screenshot
                cmd = ['gnome-screenshot', '--file=' + temp_file]
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
                
                if result.returncode == 0:
                    # Crop the specific monitor area
                    crop_cmd = ['convert', temp_file, '-crop', f'{width}x{height}+{x}+{y}', filepath]
                    crop_result = subprocess.run(crop_cmd, capture_output=True, text=True, timeout=10)
                    
                    if crop_result.returncode == 0:
                        logger.system(f"Screenshot saved: {filepath}")
                        # Clean up temp file
                        if os.path.exists(temp_file):
                            os.remove(temp_file)
                        return filepath
                    else:
                        logger.warning(f"Crop failed: {crop_result.stderr}")
                else:
                    logger.warning(f"Full screenshot failed: {result.stderr}")
            else:
                logger.warning(f"Could not find monitor: {monitor}")
        
        # Fallback to full screenshot
        try:
            result = subprocess.run([
                'gnome-screenshot', 
                '--file=' + filepath
            ], capture_output=True, text=True, timeout=15)
            
            if result.returncode == 0:
                logger.system(f"Screenshot saved: {filepath}")
                return filepath
            else:
                logger.warning(f"gnome-screenshot failed: {result.stderr}")
        except Exception as e:
            logger.warning(f"gnome-screenshot not available: {str(e)}")
        
        raise RuntimeError("No screenshot method available")
    
    def get_window_list(self) -> List[Dict]:
        """Get list of all windows with their properties including minimized/hidden ones"""
        try:
            windows = []
            
            # Method 1: Use wmctrl with -G flag for geometry
            try:
                result = subprocess.run(['wmctrl', '-l', '-G'], capture_output=True, text=True)
                if result.returncode == 0:
                    for line in result.stdout.strip().split('\n'):
                        if line:
                            parts = line.split()
                            if len(parts) >= 8:
                                window_id = parts[0]
                                desktop = parts[1]
                                x = int(parts[2])
                                y = int(parts[3])
                                width = int(parts[4])
                                height = int(parts[5])
                                window_info = ' '.join(parts[7:])
                                
                                # Get additional window state info
                                state_info = {}
                                try:
                                    state_result = subprocess.run(
                                        ['xprop', '-id', window_id, 'WM_STATE', 'WM_WINDOW_TYPE'], 
                                        capture_output=True, text=True
                                    )
                                    if state_result.returncode == 0:
                                        for state_line in state_result.stdout.split('\n'):
                                            if 'WM_STATE' in state_line:
                                                if 'WithdrawnState' in state_line:
                                                    state_info['state'] = 'minimized'
                                                elif 'IconicState' in state_line:
                                                    state_info['state'] = 'minimized'
                                                elif 'NormalState' in state_line:
                                                    state_info['state'] = 'normal'
                                            elif 'WM_WINDOW_TYPE' in state_line:
                                                if 'DOCK' in state_line:
                                                    state_info['type'] = 'dock'
                                                elif 'DESKTOP' in state_line:
                                                    state_info['type'] = 'desktop'
                                                elif 'DIALOG' in state_line:
                                                    state_info['type'] = 'dialog'
                                                else:
                                                    state_info['type'] = 'normal'
                                except:
                                    state_info = {}
                                
                                windows.append({
                                    'id': window_id,
                                    'desktop': desktop,
                                    'title': window_info,
                                    'geometry': {
                                        'x': x,
                                        'y': y,
                                        'width': width,
                                        'height': height
                                    },
                                    'state': state_info.get('state', 'unknown'),
                                    'type': state_info.get('type', 'normal')
                                })
            except Exception as e:
                logger.warning(f"wmctrl -G failed: {str(e)}")
            
            # Method 2: Use xwininfo to get all windows (fallback)
            if not windows:
                try:
                    # Get all window IDs
                    result = subprocess.run(['xwininfo', '-root', '-tree'], capture_output=True, text=True)
                    if result.returncode == 0:
                        window_ids = []
                        for line in result.stdout.split('\n'):
                            if 'Window id:' in line:
                                try:
                                    window_id = line.split('Window id:')[1].split()[0]
                                    window_ids.append(window_id)
                                except:
                                    continue
                        
                        # Get details for each window
                        for window_id in window_ids[:50]:  # Limit to avoid too many windows
                            try:
                                geom_result = subprocess.run(
                                    ['xwininfo', '-id', window_id, '-stats'], 
                                    capture_output=True, text=True
                                )
                                if geom_result.returncode == 0:
                                    geometry = {}
                                    title = f"Window {window_id}"
                                    
                                    for geom_line in geom_result.stdout.split('\n'):
                                        if 'Width:' in geom_line:
                                            geometry['width'] = int(geom_line.split(':')[1].strip())
                                        elif 'Height:' in geom_line:
                                            geometry['height'] = int(geom_line.split(':')[1].strip())
                                        elif 'Absolute upper-left X:' in geom_line:
                                            geometry['x'] = int(geom_line.split(':')[1].strip())
                                        elif 'Absolute upper-left Y:' in geom_line:
                                            geometry['y'] = int(geom_line.split(':')[1].strip())
                                        elif 'Window name:' in geom_line:
                                            title = geom_line.split('Window name:')[1].strip()
                                    
                                    if geometry and geometry.get('width', 0) > 10 and geometry.get('height', 0) > 10:
                                        windows.append({
                                            'id': window_id,
                                            'desktop': '0',
                                            'title': title,
                                            'geometry': geometry,
                                            'state': 'unknown',
                                            'type': 'normal'
                                        })
                            except:
                                continue
                except Exception as e:
                    logger.warning(f"xwininfo fallback failed: {str(e)}")
            
            return windows
        except Exception as e:
            logger.error(f"Error getting window list: {str(e)}")
            return []
    
    def focus_window(self, window_title: str) -> str:
        """Focus a window by title (partial match)"""
        try:
            windows = self.get_window_list()
            target_window = None
            
            for window in windows:
                if window_title.lower() in window['title'].lower():
                    target_window = window
                    break
            
            if target_window:
                # Use wmctrl to focus the window
                result = subprocess.run([
                    'wmctrl', '-a', target_window['title']
                ], capture_output=True, text=True)
                
                if result.returncode == 0:
                    logger.system(f"Focused window: {target_window['title']}")
                    return f"Successfully focused window: {target_window['title']}"
                else:
                    return f"Failed to focus window: {target_window['title']}"
            else:
                return f"No window found matching: {window_title}"
        
        except Exception as e:
            return f"Error focusing window: {str(e)}"
    
    def click_at_position(self, x: int, y: int, button: str = "left") -> str:
        """Click at specific screen coordinates"""
        if not PYAUTOGUI_AVAILABLE:
            return "pyautogui not available for mouse clicks"
        
        try:
            import pyautogui
            pyautogui.click(x, y, button=button)
            logger.system(f"Clicked at position ({x}, {y}) with {button} button")
            return f"Successfully clicked at position ({x}, {y})"
        except Exception as e:
            return f"Error clicking at position ({x}, {y}): {str(e)}"
    
    def type_text(self, text: str, interval: float = 0.1) -> str:
        """Type text at current cursor position"""
        if not PYAUTOGUI_AVAILABLE:
            return "pyautogui not available for typing"
        
        try:
            import pyautogui
            pyautogui.typewrite(text, interval=interval)
            logger.system(f"Typed text: {text}")
            return f"Successfully typed: {text}"
        except Exception as e:
            return f"Error typing text: {str(e)}"
    
    def press_key(self, key: str) -> str:
        """Press a specific key"""
        if not PYAUTOGUI_AVAILABLE:
            return "pyautogui not available for key presses"
        
        try:
            import pyautogui
            pyautogui.press(key)
            logger.system(f"Pressed key: {key}")
            return f"Successfully pressed key: {key}"
        except Exception as e:
            return f"Error pressing key {key}: {str(e)}"
    
    def copy_to_clipboard(self, text: str) -> str:
        """Copy text to clipboard"""
        try:
            # Use xclip for clipboard operations
            process = subprocess.Popen(['xclip', '-selection', 'clipboard'], stdin=subprocess.PIPE)
            process.communicate(input=text.encode('utf-8'))
            
            if process.returncode == 0:
                logger.system(f"Copied to clipboard: {text[:50]}...")
                return f"Successfully copied text to clipboard"
            else:
                return "Failed to copy to clipboard"
        except Exception as e:
            return f"Error copying to clipboard: {str(e)}"
    
    def paste_from_clipboard(self) -> str:
        """Paste text from clipboard"""
        try:
            result = subprocess.run(['xclip', '-selection', 'clipboard', '-o'], 
                                  capture_output=True, text=True)
            
            if result.returncode == 0:
                clipboard_text = result.stdout.strip()
                logger.system(f"Pasted from clipboard: {clipboard_text[:50]}...")
                return f"Clipboard content: {clipboard_text}"
            else:
                return "Failed to read clipboard"
        except Exception as e:
            return f"Error reading clipboard: {str(e)}"
    
    def get_screen_info(self) -> Dict:
        """Get comprehensive screen information including all monitors and visible elements"""
        try:
            screen_info = {}
            
            # Get monitor information
            monitors = self._get_monitor_info()
            screen_info['monitors'] = monitors
            
            # Get primary screen resolution
            if PYAUTOGUI_AVAILABLE:
                try:
                    import pyautogui
                    width, height = pyautogui.size()
                    screen_info['primary_resolution'] = f"{width}x{height}"
                    screen_info['primary_width'] = width
                    screen_info['primary_height'] = height
                except Exception as e:
                    logger.warning(f"pyautogui screen info failed: {str(e)}")
            
            # Get detailed display information using xrandr
            try:
                result = subprocess.run(['xrandr'], capture_output=True, text=True)
                if result.returncode == 0:
                    display_info = []
                    current_monitor = None
                    
                    for line in result.stdout.split('\n'):
                        if ' connected ' in line:
                            parts = line.split()
                            monitor_name = parts[0]
                            current_monitor = {
                                'name': monitor_name,
                                'connected': True,
                                'primary': '*' in line,
                                'resolutions': []
                            }
                            display_info.append(current_monitor)
                        elif current_monitor and 'x' in line and line.strip()[0].isdigit():
                            # Parse resolution
                            resolution = line.strip().split()[0]
                            if 'x' in resolution:
                                current_monitor['resolutions'].append(resolution)
                    
                    screen_info['displays'] = display_info
            except Exception as e:
                logger.warning(f"xrandr failed: {str(e)}")
            
            # Get desktop environment info
            try:
                desktop = os.environ.get('XDG_CURRENT_DESKTOP', 'unknown')
                screen_info['desktop_environment'] = desktop
            except:
                screen_info['desktop_environment'] = 'unknown'
            
            # Get window manager info
            try:
                result = subprocess.run(['wmctrl', '-m'], capture_output=True, text=True)
                if result.returncode == 0:
                    for line in result.stdout.split('\n'):
                        if 'Name:' in line:
                            screen_info['window_manager'] = line.split('Name:')[1].strip()
                            break
            except:
                screen_info['window_manager'] = 'unknown'
            
            # Get total screen area (all monitors combined)
            total_width = 0
            total_height = 0
            for monitor in monitors:
                if monitor.get('resolution'):
                    try:
                        width, height = map(int, monitor['resolution'].split('x'))
                        total_width = max(total_width, width)
                        total_height = max(total_height, height)
                    except:
                        pass
            
            if total_width > 0 and total_height > 0:
                screen_info['total_resolution'] = f"{total_width}x{total_height}"
                screen_info['total_width'] = total_width
                screen_info['total_height'] = total_height
            
            return screen_info
        except Exception as e:
            return {'error': f'Error getting screen info: {str(e)}'}

# Global UI automation instance
ui_automation = UIAutomation()

# Tool execution functions
async def take_screenshot(filename: str = None, monitor: str = None) -> str:
    """Take a screenshot"""
    try:
        filepath = ui_automation.take_screenshot(filename, monitor)
        return f"Screenshot saved: {filepath}"
    except Exception as e:
        return f"Error taking screenshot: {str(e)}"

async def get_window_list() -> str:
    """Get list of all windows"""
    try:
        windows = ui_automation.get_window_list()
        if windows:
            result = "Open windows:\n"
            for i, window in enumerate(windows):
                result += f"{i+1}. {window['title']}\n"
                if window['geometry']:
                    geom = window['geometry']
                    result += f"   Position: ({geom.get('x', 'N/A')}, {geom.get('y', 'N/A')})\n"
                    result += f"   Size: {geom.get('width', 'N/A')}x{geom.get('height', 'N/A')}\n"
            return result
        else:
            return "No windows found or error getting window list"
    except Exception as e:
        return f"Error getting window list: {str(e)}"

async def focus_window(window_title: str) -> str:
    """Focus a window by title"""
    return ui_automation.focus_window(window_title)

async def click_at_position(x: int, y: int, button: str = "left") -> str:
    """Click at specific coordinates"""
    return ui_automation.click_at_position(x, y, button)

async def type_text(text: str, interval: float = 0.1) -> str:
    """Type text at current cursor position"""
    return ui_automation.type_text(text, interval)

async def press_key(key: str) -> str:
    """Press a specific key"""
    return ui_automation.press_key(key)

async def copy_to_clipboard(text: str) -> str:
    """Copy text to clipboard"""
    return ui_automation.copy_to_clipboard(text)

async def paste_from_clipboard() -> str:
    """Paste text from clipboard"""
    return ui_automation.paste_from_clipboard()

async def get_screen_info() -> str:
    """Get comprehensive screen information"""
    try:
        info = ui_automation.get_screen_info()
        if 'error' in info:
            return f"Error: {info['error']}"
        
        result = "Screen Information:\n"
        
        # Primary resolution
        if 'primary_resolution' in info:
            result += f"Primary Resolution: {info['primary_resolution']}\n"
        
        # Total resolution (all monitors)
        if 'total_resolution' in info:
            result += f"Total Resolution: {info['total_resolution']}\n"
        
        # Desktop environment
        if 'desktop_environment' in info:
            result += f"Desktop Environment: {info['desktop_environment']}\n"
        
        # Window manager
        if 'window_manager' in info:
            result += f"Window Manager: {info['window_manager']}\n"
        
        # Monitor details
        if 'monitors' in info and info['monitors']:
            result += f"\nMonitors ({len(info['monitors'])}):\n"
            for i, monitor in enumerate(info['monitors']):
                result += f"  {i+1}. {monitor['name']}"
                if monitor.get('resolution'):
                    result += f" - {monitor['resolution']}"
                if monitor.get('primary', False):
                    result += " (Primary)"
                result += "\n"
        
        # Display details
        if 'displays' in info and info['displays']:
            result += f"\nDisplays ({len(info['displays'])}):\n"
            for i, display in enumerate(info['displays']):
                result += f"  {i+1}. {display['name']}"
                if display.get('primary', False):
                    result += " (Primary)"
                if display.get('resolutions'):
                    result += f" - Available: {', '.join(display['resolutions'][:3])}"
                result += "\n"
        
        return result
    except Exception as e:
        return f"Error getting screen info: {str(e)}"

# Tool definitions
def get_screenshot_tool() -> Dict:
    return {
        "type": "function",
        "function": {
            "name": "take_screenshot",
            "description": "Take a screenshot of the current screen and save it to the screenshots directory",
            "parameters": {
                "type": "object",
                "properties": {
                    "filename": {
                        "type": "string",
                        "description": "Optional filename for the screenshot (without extension)"
                    },
                    "monitor": {
                        "type": "string",
                        "description": "Monitor to capture: 'primary', 'secondary', 'all', or monitor name like 'HDMI-1'",
                        "default": "all"
                    }
                }
            }
        }
    }

def get_window_list_tool() -> Dict:
    return {
        "type": "function",
        "function": {
            "name": "get_window_list",
            "description": "Get a list of all open windows with their properties (title, position, size)",
            "parameters": {
                "type": "object",
                "properties": {}
            }
        }
    }

def get_focus_window_tool() -> Dict:
    return {
        "type": "function",
        "function": {
            "name": "focus_window",
            "description": "Focus/bring to front a window by its title (partial match supported)",
            "parameters": {
                "type": "object",
                "properties": {
                    "window_title": {
                        "type": "string",
                        "description": "Title of the window to focus (partial match supported)"
                    }
                },
                "required": ["window_title"]
            }
        }
    }

def get_click_tool() -> Dict:
    return {
        "type": "function",
        "function": {
            "name": "click_at_position",
            "description": "Click at specific screen coordinates",
            "parameters": {
                "type": "object",
                "properties": {
                    "x": {
                        "type": "integer",
                        "description": "X coordinate on screen"
                    },
                    "y": {
                        "type": "integer",
                        "description": "Y coordinate on screen"
                    },
                    "button": {
                        "type": "string",
                        "description": "Mouse button to use (left, right, middle)",
                        "default": "left"
                    }
                },
                "required": ["x", "y"]
            }
        }
    }

def get_type_text_tool() -> Dict:
    return {
        "type": "function",
        "function": {
            "name": "type_text",
            "description": "Type text at the current cursor position",
            "parameters": {
                "type": "object",
                "properties": {
                    "text": {
                        "type": "string",
                        "description": "Text to type"
                    },
                    "interval": {
                        "type": "number",
                        "description": "Delay between keystrokes in seconds",
                        "default": 0.1
                    }
                },
                "required": ["text"]
            }
        }
    }

def get_press_key_tool() -> Dict:
    return {
        "type": "function",
        "function": {
            "name": "press_key",
            "description": "Press a specific key",
            "parameters": {
                "type": "object",
                "properties": {
                    "key": {
                        "type": "string",
                        "description": "Key to press (e.g., 'enter', 'tab', 'ctrl+c', 'f5')"
                    }
                },
                "required": ["key"]
            }
        }
    }

def get_copy_to_clipboard_tool() -> Dict:
    return {
        "type": "function",
        "function": {
            "name": "copy_to_clipboard",
            "description": "Copy text to clipboard",
            "parameters": {
                "type": "object",
                "properties": {
                    "text": {
                        "type": "string",
                        "description": "Text to copy to clipboard"
                    }
                },
                "required": ["text"]
            }
        }
    }

def get_paste_from_clipboard_tool() -> Dict:
    return {
        "type": "function",
        "function": {
            "name": "paste_from_clipboard",
            "description": "Paste text from clipboard",
            "parameters": {
                "type": "object",
                "properties": {}
            }
        }
    }

def get_screen_info_tool() -> Dict:
    return {
        "type": "function",
        "function": {
            "name": "get_screen_info",
            "description": "Get screen resolution and display information",
            "parameters": {
                "type": "object",
                "properties": {}
            }
        }
    }