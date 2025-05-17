from typing import Dict, List, Any, Optional, Union
import os
import fnmatch
import sys
from mcp.server.fastmcp import FastMCP

# Print debug information
print(f"Starting Filesystem MCP Server", file=sys.stderr)
print(f"Current working directory: {os.getcwd()}", file=sys.stderr)

# Initialize the MCP server with a descriptive name
mcp = FastMCP("Filesystem MCP Server for The Plot Thickens")

@mcp.tool()
def list_directory(directory: str = '.') -> List[Dict[str, Any]]:
    """List contents of a directory.
    
    Args:
        directory: Path to list (default: current directory)
    
    Returns:
        A list of dictionaries with file information
    """
    try:
        if not os.path.exists(directory):
            return [{"error": f"Directory not found: {directory}"}]
        
        entries = []
        for entry in os.listdir(directory):
            full_path = os.path.join(directory, entry)
            entry_info = {
                "name": entry,
                "path": os.path.abspath(full_path),
                "type": "directory" if os.path.isdir(full_path) else "file",
            }
            
            if os.path.isfile(full_path):
                entry_info["size"] = os.path.getsize(full_path)
                entry_info["extension"] = os.path.splitext(entry)[1]
            
            entries.append(entry_info)
        
        return entries
    except Exception as e:
        return [{"error": str(e)}]

@mcp.tool()
def search_files(pattern: str, directory: str = ".", recursive: bool = True, include_hidden: bool = False) -> List[Dict[str, Any]]:
    """Search for files matching a pattern.
    
    Args:
        pattern: Glob pattern to match (e.g., "*.py", "data*.json")
        directory: Directory to search in (default: current directory)
        recursive: Whether to search subdirectories (default: True)
        include_hidden: Whether to include hidden files (default: False)
    
    Returns:
        A list of matching file information
    """
    try:
        if not os.path.exists(directory):
            return [{"error": f"Directory not found: {directory}"}]
        
        matches = []
        
        for root, dirs, files in os.walk(directory):
            # Skip hidden directories if not including hidden files
            if not include_hidden:
                dirs[:] = [d for d in dirs if not d.startswith('.')]
            
            for filename in files:
                if not include_hidden and filename.startswith('.'):
                    continue
                
                if fnmatch.fnmatch(filename, pattern):
                    full_path = os.path.join(root, filename)
                    matches.append({
                        "name": filename,
                        "path": os.path.abspath(full_path),
                        "size": os.path.getsize(full_path),
                        "extension": os.path.splitext(filename)[1],
                        "directory": os.path.relpath(root, directory)
                    })
            
            # If not recursive, break after the first iteration
            if not recursive:
                break
        
        return matches
    except Exception as e:
        return [{"error": str(e)}]

@mcp.tool()
def read_file_content(file_path: str, max_size: int = 100000) -> Dict[str, Any]:
    """Read the content of a file.
    
    Args:
        file_path: Path to the file
        max_size: Maximum file size to read in bytes (default: 100KB)
    
    Returns:
        A dictionary with file information and content
    """
    try:
        if not os.path.exists(file_path):
            return {"error": f"File not found: {file_path}"}
        
        if not os.path.isfile(file_path):
            return {"error": f"Not a file: {file_path}"}
        
        file_size = os.path.getsize(file_path)
        if file_size > max_size:
            return {
                "error": f"File too large ({file_size} bytes), max size is {max_size} bytes",
                "path": os.path.abspath(file_path),
                "size": file_size
            }
        
        with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
            content = f.read()
            
        return {
            "path": os.path.abspath(file_path),
            "name": os.path.basename(file_path),
            "size": file_size,
            "extension": os.path.splitext(file_path)[1],
            "content": content
        }
    except Exception as e:
        return {"error": str(e)}

@mcp.tool()
def find_in_files(search_text: str, directory: str = ".", file_pattern: str = "*", recursive: bool = True, case_sensitive: bool = False) -> List[Dict[str, Any]]:
    """Search for text within files.
    
    Args:
        search_text: Text to search for
        directory: Directory to search in (default: current directory)
        file_pattern: Glob pattern for files to include (default: all files)
        recursive: Whether to search subdirectories (default: True)
        case_sensitive: Whether the search is case-sensitive (default: False)
    
    Returns:
        A list of dictionaries with match information
    """
    try:
        if not os.path.exists(directory):
            return [{"error": f"Directory not found: {directory}"}]
        
        if not case_sensitive:
            search_text = search_text.lower()
        
        matches = []
        
        for root, _, files in os.walk(directory):
            for filename in fnmatch.filter(files, file_pattern):
                file_path = os.path.join(root, filename)
                
                try:
                    # Skip binary files and very large files
                    if os.path.getsize(file_path) > 1000000:  # 1MB limit
                        continue
                    
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        for i, line in enumerate(f, 1):
                            line_to_check = line if case_sensitive else line.lower()
                            if search_text in line_to_check:
                                matches.append({
                                    "path": os.path.abspath(file_path),
                                    "name": filename,
                                    "line_number": i,
                                    "line": line.strip(),
                                    "directory": os.path.relpath(root, directory)
                                })
                except Exception:
                    # Skip files that can't be read as text
                    continue
            
            # If not recursive, break after the first iteration
            if not recursive:
                break
        
        return matches
    except Exception as e:
        return [{"error": str(e)}]

if __name__ == "__main__":
    print("Filesystem MCP Server is running...", file=sys.stderr)
    mcp.run() 