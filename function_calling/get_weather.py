from typing import Dict, List

def get_weather_tool() -> Dict:
    return {
        "type": "function",
        "function": {
            "name": "get_weather_info",
            "description": "Get current weather information for a location",
            "parameters": {
                "type": "object",
                "properties": {
                    "location": {
                        "type": "string",
                        "description": "The city and state, e.g., San Francisco, CA"
                    }
                },
                "required": ["location"]
            }
        }
    }

async def get_weather_info(location: str) -> str:
    """
    Get weather information for a specific location
    
    Args:
        location: City and state
    
    Returns:
        Weather information string
    """
    # This is a mock implementation
    # In a real application, you would make an API call to a weather service
    return f"The weather in {location} is sunny with a temperature of 75°F."

