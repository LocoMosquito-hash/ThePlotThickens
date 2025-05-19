# Documentation Crawler MCP Server for The Plot Thickens

This MCP server provides functionality to crawl, cache, and search documentation from online sources, inspired by Cursor's documentation crawler. It allows your application to access and integrate documentation seamlessly.

## Features

- Add documentation sources with start URL and prefix URL
- Crawl documentation pages from specified sources
- Cache documentation locally for offline use
- Search through crawled documentation
- Get full content of specific documentation pages

## Usage

The Documentation Crawler MCP provides the following tools:

1. `add_doc_source` - Add a new documentation source to crawl
2. `remove_doc_source` - Remove a documentation source
3. `list_doc_sources` - List all available documentation sources
4. `crawl_documentation` - Crawl documentation from a source
5. `search_documentation` - Search through crawled documentation
6. `get_doc_content` - Get the content of a specific documentation page

## Example: Adding PyQt6 Documentation

```python
# Add PyQt6 documentation source
add_doc_source_result = docs_crawler.add_doc_source(
    name="PyQt6",
    start_url="https://doc.qt.io/qtforpython-6/",
    prefix_url="https://doc.qt.io/qtforpython-6/"
)

# Crawl documentation
crawl_result = docs_crawler.crawl_documentation(
    name="PyQt6",
    max_pages=100  # Limit to 100 pages
)

# Search for QWidget
search_result = docs_crawler.search_documentation(
    query="QWidget",
    source_name="PyQt6"  # Optional, can search across all sources
)

# Get content of a specific page
if search_result["results"]:
    url = search_result["results"][0]["url"]
    content = docs_crawler.get_doc_content(url)
```

## Requirements

This MCP server requires the `html2text` package for HTML to text conversion. Install it with:

```bash
pip install html2text
```

## Configuration

The server caches documentation in the system's temporary directory under `tpt_docs_cache`. You can modify the cache location by changing the `cache_dir` attribute in the `DocsCrawlerMCPServer` class.

## Integration with The Plot Thickens

To integrate this MCP server with The Plot Thickens, add it to your `.cursor/mcp.json` configuration:

```json
{
  "mcpServers": {
    "docs-crawler": {
      "command": "<Python Executable Path>",
      "args": ["<Path to docs_crawler_mcp_server.py>"],
      "env": {
        "PYTHONUNBUFFERED": "1"
      }
    }
  }
}
```

Replace `<Python Executable Path>` and `<Path to docs_crawler_mcp_server.py>` with the actual paths on your system.
