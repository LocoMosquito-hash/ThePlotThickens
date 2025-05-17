# Custom SQLite MCP Implementation for Cursor

This is a custom implementation of a Model Context Protocol (MCP) server for SQLite databases that works with Cursor without requiring external MCP packages.

## What's Different

Unlike the official MCP SQLite server, this implementation:

1. Doesn't require any external MCP packages
2. Runs directly using standard Python libraries
3. Provides detailed debug logs to help diagnose issues
4. Is specifically designed to work with Cursor's MCP client

## How It Works

The implementation provides a simple JSON-based protocol over stdin/stdout that Cursor can use to:

- Get the database schema
- List available tables
- Get information about specific tables
- Query data with filtering and pagination
- Execute custom SQL queries

## Configuration

The server is configured in `.cursor/mcp.json` and set up to use your `the_plot_thickens.db` database.

## Troubleshooting

If you encounter issues:

1. Check the Cursor MCP logs for errors
2. Look for debug log entries (starting with `[DEBUG]`) in the console output
3. Verify that `the_plot_thickens.db` is in the expected location
4. Restart Cursor to reload the MCP configuration

## Supported Operations

The server supports the following operations:

- `list_tables`: Get a list of all tables in the database
- `get_schema`: Get the complete database schema
- `get_table_info`: Get detailed information about a specific table
- `query_table`: Query data from a table with optional filtering
- `execute_query`: Execute a custom SQL query

## Example Usage in Cursor

After restarting Cursor, you can ask questions like:

- "What tables are in the database?"
- "Show me the schema of the characters table"
- "Get 5 rows from the events table"
- "Find all characters with 'Smith' in their name"
