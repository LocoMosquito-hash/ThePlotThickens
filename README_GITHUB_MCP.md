# GitHub MCP Server for The Plot Thickens

This MCP (Model Context Protocol) server provides Cursor with GitHub integration capabilities for The Plot Thickens application. It allows Cursor to interact with GitHub repositories, search for code, and retrieve user information.

## Setup

The MCP server is already configured and ready to use. The setup includes:

1. A Python script (`github_mcp_server.py`) that implements the MCP server with GitHub API tools
2. A Cursor configuration file (`.cursor/mcp.json`) that tells Cursor how to run the server
3. GitHub Personal Access Token for authentication

## Available Tools

The server provides the following tools that Cursor can use:

### Repository Management

- `list_repositories(username)` - Lists all repositories for a given GitHub username
- `search_repositories(query, sort="stars", order="desc", per_page=10)` - Searches for repositories matching a query
- `get_repository_content(repo_owner, repo_name, path="")` - Gets the contents of a repository at a specific path

### Code and File Access

- `get_file_content(repo_owner, repo_name, file_path)` - Gets the content of a specific file from a repository
- `search_code(query, per_page=10)` - Searches for code across GitHub using a query

### User Information

- `get_user_info(username)` - Gets information about a GitHub user

## Usage Examples

Here are some examples of how to use the GitHub MCP server with Cursor:

1. List repositories for a user:

   ```python
   repos = mcp_github_list_repositories(username="octocat")
   ```

2. Search for repositories:

   ```python
   results = mcp_github_search_repositories(query="language:python stars:>1000")
   ```

3. Get file content:

   ```python
   file_data = mcp_github_get_file_content(repo_owner="octocat", repo_name="hello-world", file_path="README.md")
   ```

4. Search for code:
   ```python
   code_results = mcp_github_search_code(query="extension:py function def in:file repo:user/repo")
   ```

## Security Note

The GitHub Personal Access Token is stored in the `github_mcp_server.py` file. In a production environment, it would be better to store this token in a secure location like an environment variable or a secure secrets manager.

## Limitations

- The GitHub API has rate limits, which may affect the performance of the MCP server if used frequently
- File contents larger than 1MB cannot be retrieved due to API and performance limitations
- Some GitHub operations require specific permissions that might not be granted by the current token
