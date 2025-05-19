#!/usr/bin/env python3
import os
import sys
import time
import json
import urllib.request
import urllib.parse

# Test the docs crawler MCP server by making direct HTTP requests

def call_mcp_tool(tool_name, **params):
    """Call an MCP tool via HTTP."""
    try:
        # MCP servers run on port 21200 by default
        url = "http://localhost:21200/v1/tools"
        
        # Prepare request data
        data = {
            "name": tool_name,
            "parameters": params
        }
        
        # Convert to JSON
        payload = json.dumps(data).encode('utf-8')
        
        # Make request
        headers = {
            'Content-Type': 'application/json',
        }
        
        req = urllib.request.Request(url, data=payload, headers=headers, method='POST')
        with urllib.request.urlopen(req) as response:
            result = json.loads(response.read().decode('utf-8'))
            return result
    except Exception as e:
        return {"error": str(e)}

def main():
    """Test the docs crawler MCP functionality."""
    print("Testing Docs Crawler MCP Server...")
    
    # List initial sources (should be empty)
    print("\n1. Listing initial sources...")
    result = call_mcp_tool("list_doc_sources")
    print(f"Initial sources: {result}")
    
    # Add PyQt6 documentation source
    print("\n2. Adding PyQt6 documentation source...")
    result = call_mcp_tool(
        "add_doc_source", 
        name="PyQt6", 
        start_url="https://doc.qt.io/qtforpython-6/",
        prefix_url="https://doc.qt.io/qtforpython-6/"
    )
    print(f"Add result: {result}")
    
    # List sources after adding
    print("\n3. Listing sources after adding PyQt6...")
    result = call_mcp_tool("list_doc_sources")
    print(f"Sources: {result}")
    
    # Crawl a small number of pages
    print("\n4. Crawling documentation (max 3 pages)...")
    result = call_mcp_tool("crawl_documentation", name="PyQt6", max_pages=3)
    print(f"Crawl result: {result}")
    
    # Search for QWidget
    print("\n5. Searching for 'QWidget'...")
    result = call_mcp_tool("search_documentation", query="QWidget", source_name="PyQt6")
    print(f"Search result count: {result.get('count', 0)}")
    
    # Display first result
    if result.get('results') and len(result['results']) > 0:
        first_result = result['results'][0]
        print("\nTop search result:")
        print(f"URL: {first_result.get('url')}")
        print(f"Score: {first_result.get('score')}")
        print(f"Context: {first_result.get('context', '')[:150]}...")
        
        # Get full content
        print("\n6. Getting full content of the top result...")
        content_result = call_mcp_tool("get_doc_content", url=first_result.get('url'))
        if content_result.get('success'):
            content = content_result.get('content', '')
            print(f"Content length: {len(content)} characters")
            print(f"Content preview: {content[:200]}...")
    else:
        print("No search results found.")
    
    # Remove the source
    print("\n7. Removing PyQt6 documentation source...")
    result = call_mcp_tool("remove_doc_source", name="PyQt6")
    print(f"Remove result: {result}")
    
    # List final sources
    print("\n8. Listing final sources...")
    result = call_mcp_tool("list_doc_sources")
    print(f"Final sources: {result}")
    
if __name__ == "__main__":
    main() 