from mcp.server.stdio import StdioMCPServer
import sqlite3
import sys
import json

# Initialize server
server = StdioMCPServer("Simple SQLite DB Server")

DB_PATH = 'the_plot_thickens.db'

@server.tool("list_tables")
async def list_tables(_params):
    """List all tables in the database."""
    print("Tool called: list_tables", file=sys.stderr)
    
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = [table[0] for table in cursor.fetchall()]
        
        conn.close()
        print(f"Found {len(tables)} tables", file=sys.stderr)
        
        return {"tables": tables}
    except Exception as e:
        print(f"Error in list_tables: {str(e)}", file=sys.stderr)
        return {"error": str(e)}

@server.tool("get_table_info")
async def get_table_info(params):
    """Get information about a specific table."""
    table_name = params.get("table_name")
    print(f"Tool called: get_table_info for {table_name}", file=sys.stderr)
    
    if not table_name:
        return {"error": "table_name parameter is required"}
    
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute(f"PRAGMA table_info({table_name});")
        columns = cursor.fetchall()
        
        conn.close()
        
        column_info = [
            {
                "name": col[1],
                "type": col[2],
                "notnull": bool(col[3]),
                "default": col[4],
                "pk": bool(col[5])
            }
            for col in columns
        ]
        
        return {"columns": column_info}
    except Exception as e:
        print(f"Error in get_table_info: {str(e)}", file=sys.stderr)
        return {"error": str(e)}

print("Starting MCP server...", file=sys.stderr)

if __name__ == "__main__":
    try:
        server.run()
    except Exception as e:
        print(f"Error running MCP server: {str(e)}", file=sys.stderr) 