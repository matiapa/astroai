import os
from googleapiclient.discovery import build

def web_search(query: str) -> dict:
    """
    Performs a web search to find information about celestial objects, astronomical events, or scientific data.
    
    Args:
        query: The search query string (e.g., "distance to Betelgeuse", "current phase of the moon").
        
    Returns:
        A text summary of the search results.
    """
    api_key = os.environ.get("GOOGLE_API_KEY")
    cse_id = os.environ.get("GOOGLE_CSE_ID")
    
    if not api_key:
        return {"success": False, "error": "GOOGLE_API_KEY environment variable not set."}
    if not cse_id:
        return {"success": False, "error": "GOOGLE_CSE_ID environment variable not set."}

    try:
        service = build("customsearch", "v1", developerKey=api_key)
        # Execute the search
        result = service.cse().list(q=query, cx=cse_id, num=5).execute()
        
        items = result.get("items", [])
        if not items:
            return {"success": False, "error": "No results found."}
        
        formatted_results = []
        for item in items:
            title = item.get("title", "No Title")
            link = item.get("link", "No Link")
            snippet = item.get("snippet", "No Snippet")
            formatted_results.append({"title": title, "link": link, "snippet": snippet})
            
        return {"success": True, "results": formatted_results}
    except Exception as e:
        return {"success": False, "error": str(e)}
