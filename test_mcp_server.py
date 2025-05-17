from mcp.server.fastmcp import FastMCP
import sys

# Initialize the MCP server
mcp = FastMCP("Test MCP Server")

print("Starting Test MCP Server...", file=sys.stderr)

@mcp.tool()
def hello_world() -> str:
    """A simple hello world function to test if the MCP server is working."""
    print("Tool called: hello_world", file=sys.stderr)
    return "Hello, world!"

@mcp.tool()
def add_numbers(a: int, b: int) -> int:
    """Add two numbers and return the result."""
    print(f"Tool called: add_numbers({a}, {b})", file=sys.stderr)
    return a + b

print("MCP server initialized, running...", file=sys.stderr)

# Run the MCP server
if __name__ == '__main__':
    try:
        mcp.run()
    except Exception as e:
        print(f"Error running MCP server: {str(e)}", file=sys.stderr) 