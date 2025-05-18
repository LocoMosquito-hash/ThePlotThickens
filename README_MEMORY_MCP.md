# Memory MCP Server for The Plot Thickens

This MCP (Model Context Protocol) server provides Cursor with persistent memory capabilities for The Plot Thickens application. It allows Cursor to store, retrieve, and manage information that persists between sessions.

## Setup

The MCP server is already configured and ready to use. The setup includes:

1. A Python script (`memory_mcp_server.py`) that implements the MCP server with memory storage tools
2. A Cursor configuration file (`.cursor/mcp.json`) that tells Cursor how to run the server
3. A JSON file (`memory_store.json`) that stores the persistent data

## Available Tools

The server provides the following tools that Cursor can use:

### Basic Memory Operations

- `store_memory(key, value)` - Stores a value with the given key
- `retrieve_memory(key)` - Retrieves a value by key
- `list_memories()` - Lists all stored memory keys
- `delete_memory(key)` - Deletes a memory by key
- `clear_memories()` - Clears all stored memories

### Hierarchical Memory Operations

- `store_complex_memory(category, key, value)` - Stores a value with category/key organization
- `retrieve_category(category)` - Retrieves all memory values in a category

## Usage Examples

Here are some examples of how to use the Memory MCP server with Cursor:

1. Store a simple memory:

   ```python
   result = mcp_memory_store_memory(key="last_user", value="John Doe")
   ```

2. Retrieve a stored memory:

   ```python
   data = mcp_memory_retrieve_memory(key="last_user")
   if data["success"]:
       user = data["value"]
   ```

3. Store structured data:

   ```python
   character = {
       "name": "Protagonist",
       "traits": ["brave", "intelligent"],
       "relationships": {
           "mentor": "Wise Old Man",
           "ally": "Sidekick"
       }
   }
   mcp_memory_store_memory(key="main_character", value=character)
   ```

4. Organize memories by category:

   ```python
   mcp_memory_store_complex_memory(
       category="characters",
       key="protagonist",
       value={"name": "Hero", "age": 25}
   )

   mcp_memory_store_complex_memory(
       category="characters",
       key="antagonist",
       value={"name": "Villain", "age": 40}
   )

   # Later retrieve all characters
   all_characters = mcp_memory_retrieve_category(category="characters")
   ```

5. List all stored memories:

   ```python
   memory_list = mcp_memory_list_memories()
   for key in memory_list["keys"]:
       print(key)
   ```

## Data Persistence

The Memory MCP server saves all memories to a file called `memory_store.json` in the same directory as the server. This ensures that memories persist between sessions.

## Security Note

The memory store is not encrypted and should not be used to store sensitive information. In a production environment, consider implementing proper encryption and secure storage mechanisms.
