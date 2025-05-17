# Filesystem MCP Server for The Plot Thickens

This MCP (Model Context Protocol) server provides Cursor with file search and navigation capabilities for The Plot Thickens application. It allows Cursor to search, list, and read files in your project directory.

## Setup

The MCP server is already configured and ready to use. The setup includes:

1. A Python script (`filesystem_mcp_server.py`) that implements the MCP server with filesystem tools
2. A Cursor configuration file (`.cursor/mcp.json`) that tells Cursor how to run the server

## Available Tools

The server provides the following tools that Cursor can use:

### Directory and File Listing

- `list_directory(directory=".")` - Lists all files and directories in the specified path
- `search_files(pattern, directory=".", recursive=True, include_hidden=False)` - Searches for files matching a pattern

### File Content

- `read_file_content(file_path, max_size=100000)` - Reads the content of a file (limited to 100KB by default)
- `find_in_files(search_text, directory=".", file_pattern="*", recursive=True, case_sensitive=False)` - Searches for text within files

## Usage in Cursor

When chatting with Cursor, you can ask questions about your files and Cursor will automatically use the appropriate MCP tools to answer your questions. For example:

- "List all Python files in the project"
- "Find all files that use PyQt6 imports"
- "Show me the content of app/main.py"
- "Find all occurrences of 'Character' class in the codebase"

## Examples

Here are some examples of how you might use this in Cursor:

```
# List files in a directory
What files are in the app directory?

# Search for files by pattern
Find all Python files in the project

# Search within files
Find all occurrences of 'SQLAlchemy' in the codebase

# Read file content
Show me the content of requirements.txt
```

## Troubleshooting

If Cursor doesn't seem to be using the MCP tools:

1. Make sure the `.cursor/mcp.json` file is correctly configured
2. Check that the `filesystem_mcp_server.py` file is executable
3. Restart Cursor to reload the MCP configuration
