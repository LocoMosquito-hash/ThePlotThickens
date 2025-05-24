from typing import Dict, List, Any, Optional, Union
import os
import sys
import requests
import json
from mcp.server.fastmcp import FastMCP

# Print debug information
print(f"Starting GitHub MCP Server", file=sys.stderr)
print(f"Current working directory: {os.getcwd()}", file=sys.stderr)

# GitHub API token - should be stored securely in production
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "")
GITHUB_API_URL = "https://api.github.com"

# Validate that the token is available
if not GITHUB_TOKEN:
    print("Warning: GITHUB_TOKEN environment variable not set. GitHub API access will be limited.", file=sys.stderr)

# Initialize the MCP server with a descriptive name
mcp = FastMCP("GitHub MCP Server for The Plot Thickens")

def get_github_headers() -> Dict[str, str]:
    """Get headers for GitHub API requests with authentication.
    
    Returns:
        Dictionary of headers including authorization
    """
    headers = {
        "Accept": "application/vnd.github.v3+json",
        "User-Agent": "ThePlotThickens-MCP-Client"
    }
    
    if GITHUB_TOKEN:
        headers["Authorization"] = f"token {GITHUB_TOKEN}"
    
    return headers

@mcp.tool()
def list_repositories(username: str) -> List[Dict[str, Any]]:
    """List GitHub repositories for a user.
    
    Args:
        username: GitHub username
    
    Returns:
        List of repositories with their details
    """
    try:
        url = f"{GITHUB_API_URL}/users/{username}/repos"
        response = requests.get(url, headers=get_github_headers())
        
        if response.status_code != 200:
            return [{"error": f"Failed to list repositories: {response.status_code} - {response.text}"}]
        
        repos = response.json()
        return [{
            "name": repo["name"],
            "description": repo.get("description", ""),
            "url": repo["html_url"],
            "stars": repo["stargazers_count"],
            "forks": repo["forks_count"],
            "language": repo.get("language", ""),
            "created_at": repo["created_at"],
            "updated_at": repo["updated_at"]
        } for repo in repos]
    
    except Exception as e:
        print(f"Error listing repositories: {str(e)}", file=sys.stderr)
        return [{"error": f"Error listing repositories: {str(e)}"}]

@mcp.tool()
def search_repositories(query: str, sort: str = "stars", order: str = "desc", per_page: int = 10) -> List[Dict[str, Any]]:
    """Search for GitHub repositories.
    
    Args:
        query: Search query
        sort: Sort field (stars, forks, updated)
        order: Sort order (asc, desc)
        per_page: Number of results per page
    
    Returns:
        List of matching repositories
    """
    try:
        url = f"{GITHUB_API_URL}/search/repositories"
        params = {
            "q": query,
            "sort": sort,
            "order": order,
            "per_page": per_page
        }
        
        response = requests.get(url, headers=get_github_headers(), params=params)
        
        if response.status_code != 200:
            return [{"error": f"Failed to search repositories: {response.status_code} - {response.text}"}]
        
        results = response.json()
        return [{
            "name": repo["name"],
            "full_name": repo["full_name"],
            "description": repo.get("description", ""),
            "url": repo["html_url"],
            "stars": repo["stargazers_count"],
            "forks": repo["forks_count"],
            "language": repo.get("language", ""),
            "created_at": repo["created_at"],
            "updated_at": repo["updated_at"]
        } for repo in results.get("items", [])]
    
    except Exception as e:
        print(f"Error searching repositories: {str(e)}", file=sys.stderr)
        return [{"error": f"Error searching repositories: {str(e)}"}]

@mcp.tool()
def get_repository_content(repo_owner: str, repo_name: str, path: str = "") -> List[Dict[str, Any]]:
    """Get contents of a GitHub repository.
    
    Args:
        repo_owner: Owner of the repository
        repo_name: Name of the repository
        path: Path within the repository (optional)
    
    Returns:
        List of files and directories at the specified path
    """
    try:
        url = f"{GITHUB_API_URL}/repos/{repo_owner}/{repo_name}/contents/{path}"
        response = requests.get(url, headers=get_github_headers())
        
        if response.status_code != 200:
            return [{"error": f"Failed to get repository content: {response.status_code} - {response.text}"}]
        
        contents = response.json()
        
        # Handle single file response
        if not isinstance(contents, list):
            contents = [contents]
            
        return [{
            "name": item["name"],
            "path": item["path"],
            "type": item["type"],  # file or dir
            "size": item.get("size", 0) if item["type"] == "file" else 0,
            "url": item["html_url"],
            "download_url": item.get("download_url", "")
        } for item in contents]
    
    except Exception as e:
        print(f"Error getting repository content: {str(e)}", file=sys.stderr)
        return [{"error": f"Error getting repository content: {str(e)}"}]

@mcp.tool()
def get_file_content(repo_owner: str, repo_name: str, file_path: str) -> Dict[str, Any]:
    """Get the content of a file from a GitHub repository.
    
    Args:
        repo_owner: Owner of the repository
        repo_name: Name of the repository
        file_path: Path to the file within the repository
    
    Returns:
        Dictionary with file content and metadata
    """
    try:
        url = f"{GITHUB_API_URL}/repos/{repo_owner}/{repo_name}/contents/{file_path}"
        response = requests.get(url, headers=get_github_headers())
        
        if response.status_code != 200:
            return {"error": f"Failed to get file content: {response.status_code} - {response.text}"}
        
        file_data = response.json()
        
        if file_data["type"] != "file":
            return {"error": "The path specified is not a file"}
        
        if file_data.get("size", 0) > 1000000:  # 1MB limit
            return {"error": "File is too large to retrieve content"}
        
        # For non-binary files, content is base64 encoded
        import base64
        content = base64.b64decode(file_data["content"]).decode("utf-8")
        
        return {
            "name": file_data["name"],
            "path": file_data["path"],
            "size": file_data["size"],
            "url": file_data["html_url"],
            "content": content
        }
    
    except Exception as e:
        print(f"Error getting file content: {str(e)}", file=sys.stderr)
        return {"error": f"Error getting file content: {str(e)}"}

@mcp.tool()
def search_code(query: str, per_page: int = 10) -> List[Dict[str, Any]]:
    """Search for code on GitHub.
    
    Args:
        query: Search query (can include repo:owner/name, language:python, etc.)
        per_page: Number of results per page
    
    Returns:
        List of code search results
    """
    try:
        url = f"{GITHUB_API_URL}/search/code"
        params = {
            "q": query,
            "per_page": per_page
        }
        
        response = requests.get(url, headers=get_github_headers(), params=params)
        
        if response.status_code != 200:
            return [{"error": f"Failed to search code: {response.status_code} - {response.text}"}]
        
        results = response.json()
        return [{
            "name": item["name"],
            "path": item["path"],
            "repository": item["repository"]["full_name"],
            "url": item["html_url"]
        } for item in results.get("items", [])]
    
    except Exception as e:
        print(f"Error searching code: {str(e)}", file=sys.stderr)
        return [{"error": f"Error searching code: {str(e)}"}]

@mcp.tool()
def get_user_info(username: str) -> Dict[str, Any]:
    """Get information about a GitHub user.
    
    Args:
        username: GitHub username
    
    Returns:
        User information
    """
    try:
        url = f"{GITHUB_API_URL}/users/{username}"
        response = requests.get(url, headers=get_github_headers())
        
        if response.status_code != 200:
            return {"error": f"Failed to get user info: {response.status_code} - {response.text}"}
        
        user_data = response.json()
        return {
            "username": user_data["login"],
            "name": user_data.get("name", ""),
            "bio": user_data.get("bio", ""),
            "company": user_data.get("company", ""),
            "location": user_data.get("location", ""),
            "email": user_data.get("email", ""),
            "public_repos": user_data["public_repos"],
            "followers": user_data["followers"],
            "following": user_data["following"],
            "created_at": user_data["created_at"],
            "updated_at": user_data["updated_at"],
            "url": user_data["html_url"]
        }
    
    except Exception as e:
        print(f"Error getting user info: {str(e)}", file=sys.stderr)
        return {"error": f"Error getting user info: {str(e)}"}

if __name__ == "__main__":
    print("GitHub MCP Server is running...", file=sys.stderr)
    mcp.run() 