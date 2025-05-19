#!/usr/bin/env python3
from typing import Dict, List, Optional, Any, Union
import os
import sys
import json
import time
import tempfile
from pathlib import Path
import urllib.request
import urllib.parse
import html2text
import re
from dataclasses import dataclass

from mcp.server.fastmcp import FastMCP

# Print debug information
print(f"Starting Docs Crawler MCP Server", file=sys.stderr)
print(f"Current working directory: {os.getcwd()}", file=sys.stderr)

# Initialize the MCP server
mcp = FastMCP("Docs Crawler MCP Server for The Plot Thickens")

# Cache for documentation sources and content
doc_sources = {}  # name -> {start_url, prefix_url}
cached_docs = {}  # name -> {url -> content}
cache_dir = Path(tempfile.gettempdir()) / "tpt_docs_cache"
cache_dir.mkdir(exist_ok=True)

@mcp.tool()
def add_doc_source(name: str, start_url: str, prefix_url: str) -> Dict[str, Any]:
    """
    Add a documentation source to crawl and cache.
    
    Args:
        name: A unique name for the documentation source
        start_url: The URL to start crawling from
        prefix_url: The URL prefix all crawled pages should be under
        
    Returns:
        Dictionary with operation status
    """
    if name in doc_sources:
        return {"success": False, "message": f"Documentation source '{name}' already exists"}
    
    doc_sources[name] = {
        "start_url": start_url,
        "prefix_url": prefix_url
    }
    return {"success": True, "message": f"Added documentation source '{name}'"}

@mcp.tool()
def remove_doc_source(name: str) -> Dict[str, Any]:
    """
    Remove a documentation source.
    
    Args:
        name: Name of the documentation source to remove
        
    Returns:
        Dictionary with operation status
    """
    if name not in doc_sources:
        return {"success": False, "message": f"Documentation source '{name}' not found"}
    
    del doc_sources[name]
    if name in cached_docs:
        del cached_docs[name]
        
    # Remove cache files
    cache_path = cache_dir / name
    if cache_path.exists():
        for file in cache_path.glob("*.html"):
            file.unlink()
        try:
            cache_path.rmdir()
        except:
            pass
        
    return {"success": True, "message": f"Removed documentation source '{name}'"}

@mcp.tool()
def list_doc_sources() -> Dict[str, Any]:
    """
    List all available documentation sources.
    
    Returns:
        Dictionary with list of documentation sources
    """
    sources = []
    for name, source in doc_sources.items():
        sources.append({
            "name": name,
            "start_url": source["start_url"],
            "prefix_url": source["prefix_url"],
            "is_cached": name in cached_docs
        })
        
    return {"success": True, "sources": sources}

@mcp.tool()
def crawl_documentation(name: str, max_pages: int = 50) -> Dict[str, Any]:
    """
    Crawl documentation from a specified source.
    
    Args:
        name: Name of the documentation source to crawl
        max_pages: Maximum number of pages to crawl
        
    Returns:
        Dictionary with crawl results
    """
    if name not in doc_sources:
        return {"success": False, "message": f"Documentation source '{name}' not found"}
    
    source = doc_sources[name]
    
    # Create a directory for this source
    source_cache_dir = cache_dir / name
    source_cache_dir.mkdir(exist_ok=True)
    
    # Simple crawler implementation
    to_visit = [source["start_url"]]
    visited = set()
    docs = {}
    count = 0
    
    while to_visit and count < max_pages:
        url = to_visit.pop(0)
        
        if url in visited or not url.startswith(source["prefix_url"]):
            continue
            
        visited.add(url)
        count += 1
        
        try:
            # Download page
            response = urllib.request.urlopen(url)
            html = response.read().decode('utf-8', errors='replace')
            
            # Convert to text
            converter = html2text.HTML2Text()
            converter.ignore_links = False
            text = converter.handle(html)
            
            # Store in memory and cache
            docs[url] = text
            
            # Cache to disk
            page_id = urllib.parse.quote_plus(url)
            cache_file = source_cache_dir / f"{page_id}.html"
            with open(cache_file, "w", encoding="utf-8", errors='replace') as f:
                f.write(html)
            
            # Extract links
            links = re.findall(r'\[.*?\]\((.*?)\)', text)
            for link in links:
                if link.startswith('/'):
                    base_url = "/".join(source["prefix_url"].split('/')[:3])  # Get domain
                    full_link = base_url + link
                elif not link.startswith(('http://', 'https://')):
                    full_link = "/".join(url.split('/')[:-1]) + '/' + link
                else:
                    full_link = link
                    
                if full_link.startswith(source["prefix_url"]) and full_link not in visited:
                    to_visit.append(full_link)
        except Exception as e:
            print(f"Error crawling {url}: {str(e)}", file=sys.stderr)
    
    # Save the crawled docs
    cached_docs[name] = docs
    
    return {
        "success": True, 
        "message": f"Crawled {count} pages from '{name}'",
        "pages_crawled": count
    }

@mcp.tool()
def search_documentation(query: str, source_name: Optional[str] = None) -> Dict[str, Any]:
    """
    Search through crawled documentation.
    
    Args:
        query: Search query
        source_name: Optional name of specific source to search
        
    Returns:
        Dictionary with search results
    """
    results = []
    sources_to_search = [source_name] if source_name else cached_docs.keys()
    
    for name in sources_to_search:
        if name not in cached_docs:
            continue
            
        docs = cached_docs[name]
        for url, content in docs.items():
            if query.lower() in content.lower():
                # Find the context around the match
                idx = content.lower().find(query.lower())
                start = max(0, idx - 100)
                end = min(len(content), idx + len(query) + 100)
                context = content[start:end]
                
                results.append({
                    "source": name,
                    "url": url,
                    "context": context,
                    "score": content.lower().count(query.lower())  # Simple relevance score
                })
    
    # Sort by relevance
    results.sort(key=lambda x: x["score"], reverse=True)
    
    return {
        "success": True,
        "count": len(results),
        "results": results[:10]  # Return top 10 results
    }

@mcp.tool()
def get_doc_content(url: str) -> Dict[str, Any]:
    """
    Get the content of a specific documentation page.
    
    Args:
        url: URL of the documentation page
        
    Returns:
        Dictionary with page content
    """
    for name, docs in cached_docs.items():
        if url in docs:
            return {
                "success": True,
                "source": name,
                "url": url,
                "content": docs[url]
            }
            
    return {"success": False, "message": f"Documentation page not found: {url}"}

if __name__ == "__main__":
    print("Docs Crawler MCP Server is running...", file=sys.stderr)
    mcp.run() 