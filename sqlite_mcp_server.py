from typing import Dict, List, Any, Optional, Union
from mcp.server.fastmcp import FastMCP
import sqlite3
import sys
import os

# Print debug information
print(f"Starting SQLite MCP Server", file=sys.stderr)
print(f"Current working directory: {os.getcwd()}", file=sys.stderr)
print(f"Database path: {os.path.abspath('the_plot_thickens.db')}", file=sys.stderr)
print(f"Database exists: {os.path.exists('the_plot_thickens.db')}", file=sys.stderr)

# Initialize the MCP server with a descriptive name
mcp = FastMCP("SQLite MCP Server for The Plot Thickens")

DB_PATH = 'the_plot_thickens.db'

def dict_factory(cursor: sqlite3.Cursor, row: tuple) -> Dict[str, Any]:
    """Convert SQLite row to dictionary with column names as keys."""
    return {col[0]: row[idx] for idx, col in enumerate(cursor.description)}

@mcp.tool()
def get_database_schema() -> Dict[str, List[Dict[str, str]]]:
    """Retrieve the schema of all tables in the database."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Get all table names
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = [table[0] for table in cursor.fetchall()]
    
    schema = {}
    for table in tables:
        cursor.execute(f"PRAGMA table_info({table});")
        columns = cursor.fetchall()
        schema[table] = [
            {
                "name": col[1],
                "type": col[2],
                "notnull": bool(col[3]),
                "default": col[4],
                "pk": bool(col[5])
            }
            for col in columns
        ]
    
    conn.close()
    return schema

@mcp.tool()
def list_tables() -> List[str]:
    """List all tables in the database."""
    print("Tool called: list_tables", file=sys.stderr)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = [table[0] for table in cursor.fetchall()]
    
    conn.close()
    print(f"Tables found: {tables}", file=sys.stderr)
    return tables

@mcp.tool()
def get_table_info(table_name: str) -> List[Dict[str, Any]]:
    """Get detailed information about a specific table."""
    print(f"Tool called: get_table_info for {table_name}", file=sys.stderr)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute(f"PRAGMA table_info({table_name});")
    columns = cursor.fetchall()
    table_info = [
        {
            "name": col[1],
            "type": col[2],
            "notnull": bool(col[3]),
            "default": col[4],
            "pk": bool(col[5])
        }
        for col in columns
    ]
    
    conn.close()
    return table_info

@mcp.tool()
def execute_query(query: str, params: Optional[List[Any]] = None) -> List[Dict[str, Any]]:
    """Execute a custom SQL query and return the results.
    
    Args:
        query: The SQL query to execute
        params: Optional parameters for the query
    
    Returns:
        A list of dictionaries representing the query results
    """
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = dict_factory
    cursor = conn.cursor()
    
    try:
        if params:
            cursor.execute(query, params)
        else:
            cursor.execute(query)
        
        results = cursor.fetchall()
        conn.close()
        return results
    except Exception as e:
        conn.close()
        return [{"error": str(e)}]

@mcp.tool()
def get_table_data(table_name: str, limit: int = 10, offset: int = 0, where_clause: str = "") -> List[Dict[str, Any]]:
    """Get data from a specific table with optional filtering.
    
    Args:
        table_name: The name of the table to query
        limit: Maximum number of rows to return (default: 10)
        offset: Number of rows to skip (default: 0)
        where_clause: Optional WHERE clause for filtering (without the 'WHERE' keyword)
    
    Returns:
        A list of dictionaries representing the table rows
    """
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = dict_factory
    cursor = conn.cursor()
    
    where_sql = f" WHERE {where_clause}" if where_clause else ""
    
    try:
        cursor.execute(f"SELECT * FROM {table_name}{where_sql} LIMIT ? OFFSET ?", (limit, offset))
        results = cursor.fetchall()
        conn.close()
        return results
    except Exception as e:
        conn.close()
        return [{"error": str(e)}]

@mcp.tool()
def get_character_details(character_id: Optional[int] = None, name: Optional[str] = None) -> Dict[str, Any]:
    """Get detailed information about a character by ID or name.
    
    Args:
        character_id: The ID of the character (optional)
        name: The name of the character (optional)
    
    Returns:
        A dictionary with character information and related entities
    """
    if character_id is None and name is None:
        return {"error": "Either character_id or name must be provided"}
    
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = dict_factory
    cursor = conn.cursor()
    
    try:
        if character_id is not None:
            cursor.execute("SELECT * FROM characters WHERE id = ?", (character_id,))
        else:
            cursor.execute("SELECT * FROM characters WHERE name LIKE ?", (f"%{name}%",))
        
        character = cursor.fetchone()
        
        if not character:
            conn.close()
            return {"error": "Character not found"}
        
        # Get character details
        cursor.execute("SELECT * FROM character_details WHERE character_id = ?", (character["id"],))
        details = cursor.fetchall()
        
        # Get events involving this character
        cursor.execute("""
            SELECT e.*
            FROM events e
            JOIN event_characters ec ON e.id = ec.event_id
            WHERE ec.character_id = ?
        """, (character["id"],))
        events = cursor.fetchall()
        
        # Get relationships
        cursor.execute("""
            SELECT r.*, c.name as target_name
            FROM relationships r
            JOIN characters c ON r.target_id = c.id
            WHERE r.source_id = ?
        """, (character["id"],))
        outgoing_relationships = cursor.fetchall()
        
        cursor.execute("""
            SELECT r.*, c.name as source_name
            FROM relationships r
            JOIN characters c ON r.source_id = c.id
            WHERE r.target_id = ?
        """, (character["id"],))
        incoming_relationships = cursor.fetchall()
        
        conn.close()
        
        return {
            "character": character,
            "details": details,
            "events": events,
            "outgoing_relationships": outgoing_relationships,
            "incoming_relationships": incoming_relationships
        }
    except Exception as e:
        conn.close()
        return {"error": str(e)}

@mcp.tool()
def search_database(query: str, tables: Optional[List[str]] = None) -> Dict[str, List[Dict[str, Any]]]:
    """Search for the given query across multiple tables.
    
    Args:
        query: The text to search for
        tables: Optional list of tables to search in. If None, searches in all text columns.
    
    Returns:
        A dictionary with table names as keys and matching rows as values
    """
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = dict_factory
    cursor = conn.cursor()
    
    if tables is None:
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = [table["name"] for table in cursor.fetchall()]
    
    results = {}
    
    for table in tables:
        # Get column info for each table
        cursor.execute(f"PRAGMA table_info({table});")
        columns = cursor.fetchall()
        
        # Filter text columns (TEXT, VARCHAR, CHAR, etc.)
        text_columns = [col["name"] for col in columns if 'TEXT' in col["type"].upper() or 'CHAR' in col["type"].upper()]
        
        if text_columns:
            search_conditions = " OR ".join([f"{col} LIKE ?" for col in text_columns])
            params = [f"%{query}%" for _ in text_columns]
            
            try:
                cursor.execute(f"SELECT * FROM {table} WHERE {search_conditions} LIMIT 20", params)
                matches = cursor.fetchall()
                
                if matches:
                    results[table] = matches
            except Exception as e:
                results[f"error_{table}"] = [{"error": str(e)}]
    
    conn.close()
    return results

print("MCP server initialized, running...", file=sys.stderr)

# Run the MCP server
if __name__ == '__main__':
    try:
        mcp.run()
    except Exception as e:
        print(f"Error running MCP server: {str(e)}", file=sys.stderr)
