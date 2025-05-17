# SQLite MCP Server for The Plot Thickens

This MCP (Model Context Protocol) server provides Cursor with direct access to the SQLite database used by The Plot Thickens application. This enables Cursor to better understand the database schema and perform queries on your behalf.

## Setup

The MCP server is already configured and ready to use. The setup includes:

1. A Python script (`sqlite_mcp_server.py`) that implements the MCP server with database access tools
2. A Cursor configuration file (`.cursor/mcp.json`) that tells Cursor how to run the server

## Available Tools

The server provides the following tools that Cursor can use:

### Database Schema and Structure

- `list_tables()` - Lists all tables in the database
- `get_database_schema()` - Retrieves the complete schema of all tables
- `get_table_info(table_name)` - Gets detailed information about a specific table

### Data Retrieval

- `get_table_data(table_name, limit, offset, where_clause)` - Retrieves data from a specific table with pagination and filtering
- `execute_query(query, params)` - Executes a custom SQL query with optional parameters
- `search_database(query, tables)` - Searches for text across multiple tables

### Application-Specific Queries

- `get_character_details(character_id, name)` - Gets comprehensive information about a character, including relationships and events

## Usage in Cursor

When chatting with Cursor, you can ask questions about your database and Cursor will automatically use the appropriate MCP tools to answer your questions. For example:

- "Show me the schema of the characters table"
- "List all tables in the database"
- "Search for 'John' in the database"
- "Get details about the character named Alice"
- "Execute a query to find all events from a specific date"

## Examples

Here are some examples of how you might use this in Cursor:

```
# Get database schema
Tell me about the database schema for this project

# List tables
What tables are in the database?

# Search for specific data
Find all characters with "Smith" in their name

# Complex queries
Show me the relationships between characters in the database

# Application-specific insights
What events is character ID 5 involved in?
```

## Troubleshooting

If Cursor doesn't seem to be using the MCP tools:

1. Make sure the `.cursor/mcp.json` file is correctly configured
2. Check that the `sqlite_mcp_server.py` file is running correctly
3. Verify that the database file `the_plot_thickens.db` is in the expected location
4. Restart Cursor to reload the MCP configuration
