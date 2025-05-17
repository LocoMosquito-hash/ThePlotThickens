#!/usr/bin/env python
"""
Wrapper script to run the MCP SQLite server
"""
import sys
import subprocess
import os
import site
import shutil

# Print debugging information
print(f"Python version: {sys.version}", file=sys.stderr)
print(f"Current working directory: {os.getcwd()}", file=sys.stderr)
print(f"Site packages: {site.getsitepackages()}", file=sys.stderr)

# Try to find mcp-server-sqlite in installed packages
mcp_path = shutil.which("mcp-server-sqlite")
if mcp_path:
    print(f"Found mcp-server-sqlite at: {mcp_path}", file=sys.stderr)
    # Run the MCP SQLite server with the database path
    result = subprocess.run([mcp_path, "--db-path", "the_plot_thickens.db"])
    sys.exit(result.returncode)
else:
    print("Could not find mcp-server-sqlite in PATH", file=sys.stderr)
    
    # Try to run it as a module
    try:
        print("Attempting to run as module...", file=sys.stderr)
        from mcp.sqlite_server import main
        sys.argv = [sys.argv[0], "--db-path", "the_plot_thickens.db"]
        main()
    except ImportError as e:
        print(f"ImportError: {e}", file=sys.stderr)
        print("Failed to import mcp.sqlite_server", file=sys.stderr)
        
        # Try a direct subprocess call to python -m
        print("Trying subprocess call to python -m...", file=sys.stderr)
        result = subprocess.run([sys.executable, "-m", "mcp.sqlite_server", "--db-path", "the_plot_thickens.db"])
        sys.exit(result.returncode) 