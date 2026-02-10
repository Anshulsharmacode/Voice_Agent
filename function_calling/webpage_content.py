from typing import Dict, Optional, Union
import aiohttp
from bs4 import BeautifulSoup
import asyncio
from urllib.parse import urlparse

def get_webpage_content_tool() -> Dict:
    return {
        "type": "function",
        "function": {
            "name": "get_webpage_content",
            "description": "Fetches and extracts the full content of any webpage or article from a given URL. Use this when you need to read or analyze the content of a specific webpage.",
            "parameters": {
                "type": "object",
                "properties": {
                    "url": {
                        "type": "string",
                        "description": "The complete URL of the webpage to extract content from (e.g., 'https://example.com/article')"
                    },
                    # "max_length": {
                    #     "type": "integer",
                    #     "description": "Maximum length of content to return",
                    #     "default": 1000
                    # }
                },
                "required": ["url"]
            }
        }
    }

async def get_webpage_content(url: str, max_length: Union[int, str] = 10000) -> str:
    """
    Get complete HTML content from a webpage
    
    Args:
        url: Webpage URL
        max_length: Maximum length of content to return (not used for HTML content)
    
    Returns:
        Complete HTML content as string
    """
    try:
        
        # Add headers to mimic a browser request
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
        }

        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers, timeout=10) as response:
                if response.status != 200:
                    return f"Error: Could not fetch webpage (Status code: {response.status})"
                
                html = await response.text()
                return html

    except aiohttp.ClientError as e:
        return f"Error accessing webpage: {str(e)}"
    except Exception as e:
        return f"Error processing webpage: {str(e)}"