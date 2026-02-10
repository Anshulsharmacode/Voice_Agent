import webbrowser
import urllib.parse
from typing import Dict, Optional
from logs import logger

def get_open_browser_tool() -> Dict:
    return {
        "type": "function",
        "function": {
            "name": "open_browser",
            "description": "Open a web browser with a search query or specific URL. Can open YouTube, Google, or any website with search functionality.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The search query or URL to open in the browser"
                    },
                    "website": {
                        "type": "string",
                        "description": "The website to search on (e.g., 'youtube', 'google', 'bing', 'duckduckgo'). Defaults to 'google'",
                        "default": "google"
                    },
                    "search_type": {
                        "type": "string",
                        "description": "Type of search - 'search' for web search, 'video' for video search, 'image' for image search",
                        "default": "search"
                    }
                },
                "required": ["query"]
            }
        }
    }

async def open_browser(query: str, website: str = "google", search_type: str = "search") -> str:
    """
    Open a web browser with a search query or specific URL
    
    Args:
        query: The search query or URL to open
        website: The website to search on (youtube, google, bing, duckduckgo, etc.)
        search_type: Type of search (search, video, image)
    
    Returns:
        String confirmation of the action
    """
    try:
        # Handle different websites and search types
        if website.lower() == "youtube":
            if search_type.lower() == "video":
                # YouTube video search
                search_url = f"https://www.youtube.com/results?search_query={urllib.parse.quote(query)}"
            else:
                # YouTube general search
                search_url = f"https://www.youtube.com/results?search_query={urllib.parse.quote(query)}"
        
        elif website.lower() == "google":
            if search_type.lower() == "video":
                # Google video search
                search_url = f"https://www.google.com/search?q={urllib.parse.quote(query)}&tbm=vid"
            elif search_type.lower() == "image":
                # Google image search
                search_url = f"https://www.google.com/search?q={urllib.parse.quote(query)}&tbm=isch"
            else:
                # Google web search
                search_url = f"https://www.google.com/search?q={urllib.parse.quote(query)}"
        
        elif website.lower() == "bing":
            if search_type.lower() == "video":
                search_url = f"https://www.bing.com/videos/search?q={urllib.parse.quote(query)}"
            elif search_type.lower() == "image":
                search_url = f"https://www.bing.com/images/search?q={urllib.parse.quote(query)}"
            else:
                search_url = f"https://www.bing.com/search?q={urllib.parse.quote(query)}"
        
        elif website.lower() == "duckduckgo":
            search_url = f"https://duckduckgo.com/?q={urllib.parse.quote(query)}"
        
        elif website.lower() == "github":
            search_url = f"https://github.com/search?q={urllib.parse.quote(query)}"
        
        elif website.lower() == "stackoverflow":
            search_url = f"https://stackoverflow.com/search?q={urllib.parse.quote(query)}"
        
        elif website.lower() == "reddit":
            search_url = f"https://www.reddit.com/search/?q={urllib.parse.quote(query)}"
        
        elif website.lower() == "wikipedia":
            search_url = f"https://en.wikipedia.org/wiki/Special:Search?search={urllib.parse.quote(query)}"
        
        else:
            # Default to Google search
            search_url = f"https://www.google.com/search?q={urllib.parse.quote(query)}"
        
        # Check if the query is already a URL
        if query.startswith(('http://', 'https://')):
            search_url = query
        
        # Open the browser
        webbrowser.open(search_url)
        
        logger.info(f"Opened browser with URL: {search_url}")
        
        return f"Successfully opened {website} in your default web browser with the query: '{query}'. The browser should now display the search results."
    
    except Exception as e:
        error_msg = f"Error opening browser: {str(e)}"
        logger.error(error_msg)
        return error_msg 