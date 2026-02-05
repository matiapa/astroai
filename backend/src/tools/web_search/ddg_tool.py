from duckduckgo_search import DDGS

def web_search(query: str) -> dict:
    """
    Performs a web search to find information about celestial objects, astronomical events, or scientific data.
    
    Args:
        query: The search query string (e.g., "distance to Betelgeuse", "current phase of the moon").
        
    Returns:
        A text summary of the search results.
    """
    try:
        results = DDGS().text(query, max_results=5)
        if not results:
            return {"success": False, "error": "No results found."}
        
        formatted_results = []
        for result in results:
            formatted_results.append({"title": result['title'], "link": result['href'], "snippet": result['body']})
            
        return {"success": True, "results": formatted_results}
    except Exception as e:
        return {"success": False, "error": str(e)}
