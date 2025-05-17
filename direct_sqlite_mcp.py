#!/usr/bin/env python
"""
Direct implementation of a simple SQLite MCP server
that doesn't rely on external MCP packages.
"""
import sys
import json
import sqlite3
import os

# Constants
DB_PATH = "the_plot_thickens.db"
DEBUG = True

def log(msg):
    """Log message to stderr for debugging"""
    if DEBUG:
        print(f"[DEBUG] {msg}", file=sys.stderr)

def dict_factory(cursor, row):
    """Convert SQLite row to dictionary with column names as keys"""
    return {col[0]: row[idx] for idx, col in enumerate(cursor.description)}

def handle_request(request_json):
    """Handle incoming JSON request and return response"""
    try:
        request = json.loads(request_json)
        action = request.get("action")
        
        if action == "get_schema":
            return get_schema()
        elif action == "list_tables":
            return list_tables()
        elif action == "get_table_info":
            table_name = request.get("table_name")
            return get_table_info(table_name)
        elif action == "query_table":
            table_name = request.get("table_name")
            limit = request.get("limit", 10)
            offset = request.get("offset", 0)
            where = request.get("where", "")
            return query_table(table_name, limit, offset, where)
        elif action == "execute_query":
            query = request.get("query")
            params = request.get("params", [])
            return execute_query(query, params)
        else:
            return {"error": f"Unknown action: {action}"}
    except Exception as e:
        log(f"Error handling request: {str(e)}")
        return {"error": str(e)}

def list_tables():
    """List all tables in the database"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = [table[0] for table in cursor.fetchall()]
        conn.close()
        
        return {"tables": tables}
    except Exception as e:
        log(f"Error listing tables: {str(e)}")
        return {"error": str(e)}

def get_schema():
    """Get the complete database schema"""
    try:
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
        return {"schema": schema}
    except Exception as e:
        log(f"Error getting schema: {str(e)}")
        return {"error": str(e)}

def get_table_info(table_name):
    """Get detailed information about a specific table"""
    if not table_name:
        return {"error": "table_name is required"}
    
    try:
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
        return {"table_info": table_info}
    except Exception as e:
        log(f"Error getting table info: {str(e)}")
        return {"error": str(e)}

def query_table(table_name, limit=10, offset=0, where=""):
    """Query data from a table with optional filtering"""
    if not table_name:
        return {"error": "table_name is required"}
    
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = dict_factory
        cursor = conn.cursor()
        
        where_clause = f" WHERE {where}" if where else ""
        query = f"SELECT * FROM {table_name}{where_clause} LIMIT ? OFFSET ?"
        
        cursor.execute(query, (limit, offset))
        results = cursor.fetchall()
        
        conn.close()
        return {"results": results}
    except Exception as e:
        log(f"Error querying table: {str(e)}")
        return {"error": str(e)}

def execute_query(query, params=None):
    """Execute a custom SQL query"""
    if not query:
        return {"error": "query is required"}
    
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = dict_factory
        cursor = conn.cursor()
        
        if params:
            cursor.execute(query, params)
        else:
            cursor.execute(query)
        
        results = cursor.fetchall()
        conn.close()
        
        return {"results": results}
    except Exception as e:
        log(f"Error executing query: {str(e)}")
        return {"error": str(e)}

def run_server():
    """Run the MCP server, reading and responding to JSON on stdin/stdout"""
    log(f"Starting SQLite MCP Server")
    log(f"Current working directory: {os.getcwd()}")
    log(f"Database path: {os.path.abspath(DB_PATH)}")
    log(f"Database exists: {os.path.exists(DB_PATH)}")
    
    while True:
        try:
            # Read a line from stdin
            request_line = sys.stdin.readline()
            if not request_line:
                log("Empty input, exiting")
                break
                
            log(f"Received request: {request_line.strip()}")
            
            # Process the request
            response = handle_request(request_line)
            
            # Send the response
            response_json = json.dumps(response)
            log(f"Sending response: {response_json}")
            print(response_json, flush=True)
            
        except Exception as e:
            log(f"Error in server loop: {str(e)}")
            response = {"error": str(e)}
            print(json.dumps(response), flush=True)

if __name__ == "__main__":
    run_server() 