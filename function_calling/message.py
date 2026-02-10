
from typing import Dict


def get_message_tool() -> Dict:
    return {
        "type": "function",
        "function": {
            "name": "generic_response",
            "description": "Sends a text message response to the user",
            "parameters": {
                "type": "object",
                "properties": {
                    "message": {
                        "type": "string",
                        "description": "The message to send to the user"
                    }
                },
                "required": ["message"]
            }
        }
    }

async def generic_response(message: str) -> str:
    """Send a text message response to the user"""
    try:
        if not isinstance(message, str):
            raise ValueError("Message must be a string")
        return message
    except Exception as e:
        raise ValueError(f"Message error: {str(e)}")