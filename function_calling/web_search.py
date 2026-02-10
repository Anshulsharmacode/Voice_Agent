from typing import Dict, List, Optional, Union
import aiohttp
import json
from bs4 import BeautifulSoup
import os
from logs import logger
from duckduckgo_search import DDGS
def get_web_search_tool() -> Dict:
    return {
        "type": "function",
        "function": {
            "name": "search_web",
            "description": "Search the web and return a list of results similar to Google and DuckDuckGo search results",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The search query"
                    },
                    "num_results": {
                        "type": "integer",
                        "description": "Number of search results to return (max 10)",
                        "default": 3
                    }
                },
                "required": ["query"]
            }
        }
    }

async def search_web(query: str, num_results: Union[int, str] = 3) -> str:
    """
    Search the web using DuckDuckGo
    
    Args:
        query: Search query
        num_results: Number of results to return (default: 3, max: 10)
    
    Returns:
        String containing search results
    """
    try:
        # Convert num_results to int if it's a string
        if isinstance(num_results, str):
            num_results = int(num_results)
        
        # Ensure num_results is within bounds
        num_results = min(max(1, num_results), 10)
        
        # Use DuckDuckGo search
        formatted_results = []
        with DDGS() as ddgs:
            for i, result in enumerate(ddgs.text(query, max_results=num_results), 1):
                try:
                    # Extract available fields with fallbacks
                    title = result.get('title', 'No title')
                    snippet = result.get('body', result.get('snippet', 'No description available'))
                    url = result.get('href', result.get('url', 'No URL available'))
                    
                    formatted_results.append(
                        f"{i}. {title}\n"
                        f"   {snippet}\n"
                        f"   URL: {url}\n"
                    )
                except Exception as e:
                    logger.error(f"Error formatting result {i}: {e}")
                    continue
        
        if not formatted_results:
            return "No results found."
        
        return "\n".join(formatted_results)
    
    except ValueError as e:
        return f"Error: Invalid number format for num_results: {str(e)}"
    except Exception as e:
        return f"Error performing web search: {str(e)}\nPlease try again with a different query."