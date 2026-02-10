from typing import Dict


def get_finish_tool() -> Dict:
    return {
        "type": "function",
        "function": {
            "name": "end_conversation",
            "description": "Call this tool when you have completed all the tasks and want to end the conversation.",
            "parameters": {
                "type": "object",
                "properties": {
                    "message": {
                        "type": "string",
                        "description": "Optional completion message"
                    }
                }
            }
        }
    }

async def end_conversation(message: str = "Task completed") -> str:
    """
    A tool to signal that the current task is complete
    Args:
        message: Optional completion message
    Returns:
        The completion message
    """
    return message