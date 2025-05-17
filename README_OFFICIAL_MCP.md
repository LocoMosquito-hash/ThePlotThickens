# Official MCP SQLite Server for The Plot Thickens

This README explains how to use the official Model Context Protocol (MCP) SQLite server with The Plot Thickens application.

## Setup

1. We've installed the official `mcp-server-sqlite` package, which provides a standardized MCP server for SQLite databases.

2. The server has been configured in `.cursor/mcp.json` to use your `the_plot_thickens.db` database.

## How It Works

The official MCP SQLite server provides the following capabilities:

- Automatic schema detection from your SQLite database
- Standard query interface for all tables
- Secure and optimized database access
- Works with Cursor's built-in MCP client

## Usage in Cursor

After restarting Cursor, you should see "official-sqlite" in the MCP Servers panel. Cursor will automatically use this server to:

1. Understand your database schema
2. Run queries on your database
3. Provide context-aware assistance for database-related tasks

## Example Queries

Here are some examples of what you can ask Cursor:

- "What tables are in the database?"
- "Show me the schema of the characters table"
- "How many events are associated with character ID 5?"
- "Find all characters with 'Smith' in their name"
- "Show me the relationships between characters"

## Troubleshooting

If you encounter issues with the MCP server:

1. Check that Cursor is properly detecting the server in the MCP Servers panel
2. Verify that `the_plot_thickens.db` is in the expected location
3. Try running `mcp-server-sqlite --db-path the_plot_thickens.db` manually to see if there are any errors
4. Restart Cursor to reload the MCP configuration

## Additional Information

For more information about the official MCP SQLite server, visit:
https://github.com/modelcontextprotocol/servers/tree/main/src/sqlite
