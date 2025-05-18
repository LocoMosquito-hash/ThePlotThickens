from typing import Dict, List, Any, Optional, Union
import os
import sys
import json
from mcp.server.fastmcp import FastMCP

# Print debug information
print(f"Starting Memory MCP Server", file=sys.stderr)
print(f"Current working directory: {os.getcwd()}", file=sys.stderr)

# Initialize the MCP server with a descriptive name
mcp = FastMCP("Memory MCP Server for The Plot Thickens")

# Store memories in a simple dict
# In a production environment, this would be backed by a database
memories: Dict[str, Any] = {}
memory_file = "memory_store.json"

# Load existing memories if available
try:
    if os.path.exists(memory_file):
        with open(memory_file, 'r') as f:
            memories = json.load(f)
        print(f"Loaded {len(memories)} memories from {memory_file}", file=sys.stderr)
except Exception as e:
    print(f"Error loading memories: {str(e)}", file=sys.stderr)

def save_memories() -> None:
    """Save memories to disk."""
    try:
        with open(memory_file, 'w') as f:
            json.dump(memories, f, indent=2)
        print(f"Saved {len(memories)} memories to {memory_file}", file=sys.stderr)
    except Exception as e:
        print(f"Error saving memories: {str(e)}", file=sys.stderr)

@mcp.tool()
def store_memory(key: str, value: Any) -> Dict[str, Any]:
    """Store a memory value with the given key.
    
    Args:
        key: The key to store the memory under
        value: The value to store
    
    Returns:
        A dictionary with success status and the stored key
    """
    try:
        memories[key] = value
        save_memories()
        return {
            "success": True,
            "key": key,
            "message": f"Successfully stored memory with key '{key}'"
        }
    except Exception as e:
        print(f"Error storing memory: {str(e)}", file=sys.stderr)
        return {
            "success": False,
            "key": key,
            "error": f"Error storing memory: {str(e)}"
        }

@mcp.tool()
def retrieve_memory(key: str) -> Dict[str, Any]:
    """Retrieve a memory value by key.
    
    Args:
        key: The key to retrieve
    
    Returns:
        A dictionary with the retrieved value or error
    """
    try:
        if key in memories:
            return {
                "success": True,
                "key": key,
                "value": memories[key]
            }
        else:
            return {
                "success": False,
                "key": key,
                "error": f"Memory with key '{key}' not found"
            }
    except Exception as e:
        print(f"Error retrieving memory: {str(e)}", file=sys.stderr)
        return {
            "success": False,
            "key": key,
            "error": f"Error retrieving memory: {str(e)}"
        }

@mcp.tool()
def list_memories() -> Dict[str, Any]:
    """List all stored memory keys.
    
    Returns:
        A dictionary with all memory keys
    """
    try:
        return {
            "success": True,
            "keys": list(memories.keys()),
            "count": len(memories)
        }
    except Exception as e:
        print(f"Error listing memories: {str(e)}", file=sys.stderr)
        return {
            "success": False,
            "error": f"Error listing memories: {str(e)}"
        }

@mcp.tool()
def delete_memory(key: str) -> Dict[str, Any]:
    """Delete a memory by key.
    
    Args:
        key: The key to delete
    
    Returns:
        A dictionary with success status
    """
    try:
        if key in memories:
            del memories[key]
            save_memories()
            return {
                "success": True,
                "key": key,
                "message": f"Successfully deleted memory with key '{key}'"
            }
        else:
            return {
                "success": False,
                "key": key,
                "error": f"Memory with key '{key}' not found"
            }
    except Exception as e:
        print(f"Error deleting memory: {str(e)}", file=sys.stderr)
        return {
            "success": False,
            "key": key,
            "error": f"Error deleting memory: {str(e)}"
        }

@mcp.tool()
def clear_memories() -> Dict[str, Any]:
    """Clear all stored memories.
    
    Returns:
        A dictionary with success status
    """
    try:
        count = len(memories)
        memories.clear()
        save_memories()
        return {
            "success": True,
            "count": count,
            "message": f"Successfully cleared {count} memories"
        }
    except Exception as e:
        print(f"Error clearing memories: {str(e)}", file=sys.stderr)
        return {
            "success": False,
            "error": f"Error clearing memories: {str(e)}"
        }

@mcp.tool()
def store_complex_memory(category: str, key: str, value: Any) -> Dict[str, Any]:
    """Store a memory value with category and key organization.
    
    Args:
        category: Category of the memory
        key: The key within the category
        value: The value to store
    
    Returns:
        A dictionary with success status and the stored path
    """
    try:
        if category not in memories:
            memories[category] = {}
        
        memories[category][key] = value
        save_memories()
        return {
            "success": True,
            "category": category,
            "key": key,
            "message": f"Successfully stored memory at '{category}/{key}'"
        }
    except Exception as e:
        print(f"Error storing complex memory: {str(e)}", file=sys.stderr)
        return {
            "success": False,
            "category": category,
            "key": key,
            "error": f"Error storing complex memory: {str(e)}"
        }

@mcp.tool()
def retrieve_category(category: str) -> Dict[str, Any]:
    """Retrieve all memory values in a category.
    
    Args:
        category: The category to retrieve
    
    Returns:
        A dictionary with all values in the category
    """
    try:
        if category in memories and isinstance(memories[category], dict):
            return {
                "success": True,
                "category": category,
                "values": memories[category],
                "count": len(memories[category])
            }
        else:
            return {
                "success": False,
                "category": category,
                "error": f"Category '{category}' not found or is not a dictionary"
            }
    except Exception as e:
        print(f"Error retrieving category: {str(e)}", file=sys.stderr)
        return {
            "success": False,
            "category": category,
            "error": f"Error retrieving category: {str(e)}"
        }

if __name__ == "__main__":
    print("Memory MCP Server is running...", file=sys.stderr)
    mcp.run() 