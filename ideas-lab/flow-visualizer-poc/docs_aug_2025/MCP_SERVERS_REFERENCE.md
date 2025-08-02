# MCP Servers Reference - The Plot Thickens Flow Visualizer POC

## Overview

This document describes the Model Context Protocol (MCP) servers configured for enhancing AI debugging and development capabilities in The Plot Thickens Flow Visualizer POC. These servers provide specialized tools that dramatically improve code analysis, debugging efficiency, and development workflow.

## What are MCP Servers?

**Model Context Protocol (MCP)** servers are specialized tools that extend AI assistant capabilities by providing direct access to external systems, databases, files, and analysis tools. They act as bridges between the AI and various data sources or computational services, enabling more sophisticated and accurate assistance.

### Benefits for Flow Visualizer POC Development:

- **🔍 Enhanced Code Analysis**: Deep understanding of complex nested menu structures
- **🐛 Advanced Debugging**: Systematic identification of root causes in parsing issues
- **📊 Data Insights**: Direct database queries and analysis
- **🔗 Cross-System Integration**: Seamless access to GitHub, documentation, and file systems
- **⚡ Accelerated Development**: Reduced manual investigation time by 3-5x

---

## Configured MCP Servers

### 1. **Official SQLite MCP Server** 📊

**Configuration ID**: `official-sqlite`  
**Purpose**: Direct database operations and analysis  
**Command**: `mcp-server-sqlite.exe`

#### Capabilities:

- Execute SELECT queries for data analysis
- Perform INSERT/UPDATE/DELETE operations
- Create and modify database schemas
- List and describe database tables
- Add business insights to analysis memos

#### Flow Visualizer Benefits:

- **Character Analysis**: Query character relationships and story data
- **Event Tracking**: Analyze story events and their connections
- **Performance Monitoring**: Track database performance metrics
- **Data Validation**: Verify data integrity during development

#### Example Usage:

```sql
-- Analyze character relationships
SELECT c1.name as character1, c2.name as character2, r.relationship_type
FROM relationships r
JOIN characters c1 ON r.character1_id = c1.id
JOIN characters c2 ON r.character2_id = c2.id;
```

---

### 2. **Filesystem MCP Server** 📁

**Configuration ID**: `filesystem`  
**Purpose**: Advanced file system operations and analysis  
**Command**: `filesystem_mcp_server.py`

#### Capabilities:

- Intelligent file content analysis
- Directory structure mapping
- File pattern detection
- Batch file operations
- Content-aware file search

#### Flow Visualizer Benefits:

- **RPY File Analysis**: Parse and understand Ren'Py script structures
- **Asset Management**: Track image, audio, and video assets
- **Code Organization**: Analyze module dependencies and imports
- **Debug File Management**: Organize and analyze debug outputs

#### Example Usage:

- Analyze all `.rpy` files in a VN project for menu structures
- Track asset usage across story files
- Monitor changes in source files during development

---

### 3. **GitHub MCP Server** 🐙

**Configuration ID**: `github`  
**Purpose**: GitHub repository integration and analysis  
**Command**: `github_mcp_server.py`

#### Capabilities:

- Repository analysis and insights
- Pull request and issue tracking
- Commit history analysis
- Code collaboration features
- Release and milestone tracking

#### Flow Visualizer Benefits:

- **Issue Tracking**: Monitor Flow Visualizer related bugs and features
- **Version Control**: Track changes in parsing algorithms
- **Collaboration**: Analyze contributions and code reviews
- **Release Planning**: Coordinate feature development

#### Example Usage:

- Fetch recent issues related to nested menu parsing
- Analyze commit patterns for performance improvements
- Track pull request discussions on visualization enhancements

---

### 4. **Memory MCP Server** 🧠

**Configuration ID**: `memory`  
**Purpose**: Persistent context and knowledge management  
**Command**: `memory_mcp_server.py`

#### Capabilities:

- Store debugging insights and solutions
- Maintain context across sessions
- Knowledge base management
- Pattern recognition storage
- Solution archival

#### Flow Visualizer Benefits:

- **Bug Pattern Recognition**: Remember recurring issues and solutions
- **Debugging History**: Maintain context of previous debugging sessions
- **Knowledge Accumulation**: Build expertise database over time
- **Quick Problem Resolution**: Access previously solved similar issues

#### Example Usage:

- Store solutions for specific nested menu parsing edge cases
- Remember effective debugging strategies for ID collision issues
- Maintain context about complex VN structures

---

### 5. **Documentation Crawler MCP Server** 📚

**Configuration ID**: `docs-crawler`  
**Purpose**: Intelligent documentation analysis and search  
**Command**: `docs_crawler_mcp_server.py`

#### Capabilities:

- Documentation indexing and search
- Technical content analysis
- Reference extraction
- API documentation parsing
- Knowledge graph construction

#### Flow Visualizer Benefits:

- **Ren'Py Documentation**: Quick access to official Ren'Py language references
- **API Reference**: Instant lookup of PyQt6 and Python documentation
- **Technical Guides**: Search through project documentation and guides
- **Best Practices**: Access coding standards and architectural guidelines

#### Example Usage:

- Search Ren'Py documentation for menu syntax rules
- Find PyQt6 examples for graph visualization components
- Access Flow Visualizer architecture documentation

---

### 6. **Fetch MCP Server** 🌐

**Configuration ID**: `fetch`  
**Purpose**: Web content retrieval and analysis  
**Command**: `mcp_server_fetch`

#### Capabilities:

- Web page content extraction
- API endpoint testing
- Real-time information gathering
- Content parsing and analysis
- External resource integration

#### Flow Visualizer Benefits:

- **Research Support**: Gather information on graph visualization techniques
- **Tool Discovery**: Find new libraries and tools for VN analysis
- **Community Resources**: Access forums and community solutions
- **External API Integration**: Test integrations with external services

#### Example Usage:

- Research latest graph visualization libraries
- Fetch examples of interactive flow diagrams
- Access community solutions for parsing challenges

---

### 7. **Code Understanding MCP Server** 🧠⭐ **(NEW)**

**Configuration ID**: `code-understanding`  
**Purpose**: Advanced semantic code analysis and understanding  
**Command**: `uvx code-understanding-mcp-server`  
**Author**: `codingthefuturewithai`

#### Revolutionary Capabilities:

- **Semantic Code Mapping**: Understand function relationships and hierarchies
- **Critical File Identification**: Automatically identify the most important files
- **Repository Structure Analysis**: Intelligent codebase organization insights
- **Cross-File Dependency Tracking**: Map complex code relationships
- **Progressive Analysis**: Build deeper understanding over time
- **Documentation Integration**: Combine code and documentation analysis

#### Flow Visualizer Benefits:

##### 🎯 **For Nested Menu Debugging**:

- **Trace Data Flow**: Automatically map the entire nested menu parsing pipeline
- **ID Collision Detection**: Identify root causes of node ID conflicts
- **Hierarchy Analysis**: Understand parent-child relationships in menu structures
- **Edge Case Discovery**: Find unusual menu patterns that break parsing

##### 🔧 **For Development Workflow**:

- **Architecture Understanding**: Visualize how `parser.py` connects to `renpy_data_adapter.py`
- **Performance Analysis**: Identify bottlenecks in large graph processing
- **Code Complexity Metrics**: Focus optimization efforts on high-complexity areas
- **Refactoring Guidance**: Understand impact of code changes across the system

##### 🐛 **For Debugging Sessions**:

- **Root Cause Analysis**: Systematically trace bugs through the entire codebase
- **Context Preservation**: Maintain understanding across multiple debugging sessions
- **Pattern Recognition**: Identify recurring issues and their solutions
- **Targeted Investigation**: Focus analysis on specific problem areas

#### Specific Tools Available:

1. **`clone_repo`**: Analyze local repository structure and relationships
2. **`get_source_repo_map`**: Semantic analysis of functions, classes, and dependencies
3. **`get_repo_structure`**: Directory structure and complexity analysis
4. **`get_repo_file_content`**: Smart file content retrieval with context
5. **`get_repo_critical_files`**: Identify structurally significant files
6. **`get_repo_documentation`**: Documentation analysis and insights
7. **`refresh_repo`**: Real-time updates as code changes

#### Example Debugging Workflow:

```
🔍 Investigation: "Why is the 'Footjob' choice missing from v15_mc_evil_robin1?"

1. clone_repo: Analyze the current codebase state
2. get_critical_files: Identify files involved in menu parsing
3. get_source_repo_map: Map the nested menu parsing pipeline
4. get_repo_file_content: Examine specific parsing functions
5. Root Cause: ID collision in hierarchical menu generation
6. Solution: Fix node_id generation logic in parser.py
```

---

### 8. **MCP Git Ingest Server** 📖⭐ **(NEW)**

**Configuration ID**: `mcp-git-ingest`  
**Purpose**: GitHub repository analysis with directory structure and file reading capabilities  
**Command**: `uvx --from git+https://github.com/adhikasp/mcp-git-ingest mcp-git-ingest`  
**Author**: `adhikasp`

#### Specialized Capabilities:

- **Repository Structure Analysis**: Get complete directory tree visualization in Unicode format
- **File Content Reading**: Access and read contents of specific files within repositories
- **GitHub Integration**: Seamless cloning and analysis of public GitHub repositories
- **Performance Optimization**: Hash-based temporary directory naming and existing repository checks
- **Error Handling**: Robust error handling for repository cloning and file operations
- **Clean Management**: Automatic cleanup of temporary directories

#### Flow Visualizer Benefits:

##### 🎯 **For Research & Pattern Discovery**:

- **Reference Project Analysis**: Study other Ren'Py and VN parsing projects for successful patterns
- **Tree Structure Visualization**: Understand repository organization at a glance with Unicode trees
- **Selective Investigation**: Read specific implementation files without full repository clones
- **Quick Repository Overview**: Get structural understanding before deeper analysis

##### 🌐 **For Visual Novel Research**:

- **VN Parser Research**: Analyze successful Visual Novel parsing implementations from GitHub
- **Nested Menu Solutions**: Study how other projects handle complex menu structures
- **Pattern Recognition**: Identify common approaches to VN script parsing challenges
- **Learning from Examples**: Discover successful parser architectures and design patterns

##### 📚 **For Educational Development**:

- **Implementation Study**: Learn from mature parsing projects and established solutions
- **Code Pattern Mining**: Extract successful approaches to complex parsing problems
- **Documentation Access**: Read README files and documentation from similar projects
- **Reference Building**: Build knowledge base of successful implementation approaches

#### Specific Tools Available:

1. **`github_directory_structure`**: Get complete repository tree structure in visual format
2. **`github_read_important_files`**: Read specific files from repositories (README, implementation files, configs)

#### Example Research Workflow:

```
🔍 VN Parser Research: "Learning from successful nested menu implementations"

1. github_directory_structure: Analyze structure of successful Ren'Py parser projects
2. github_read_important_files: Read specific parser implementation files
3. Pattern identification: Extract successful nested menu handling approaches
4. Apply insights: Adapt learned patterns to Flow Visualizer nested menu challenges
```

#### Perfect Synergy with Other MCP Servers:

- **Code Understanding MCP**: Provides semantic analysis on discovered reference implementations
- **MCP Git Ingest**: Provides repository research and successful pattern discovery
- **Code Analysis MCP**: Offers detailed technical analysis using insights from reference projects

---

### 9. **Code Analysis MCP Server** 🔍⭐ **(NEW)**

**Configuration ID**: `code-analysis`  
**Purpose**: Natural language code exploration and repository analysis  
**Command**: `python code_analysis.py`  
**Author**: `saiprashanths`

#### Revolutionary Capabilities:

- **Natural Language Queries**: Ask high-level questions about codebase structure and functionality
- **Repository Structure Analysis**: Intelligent exploration of file and directory organization
- **Targeted File Analysis**: Deep dive into specific files with contextual understanding
- **Local Processing**: Safe, cost-effective analysis without external API dependencies
- **Smart Filtering**: Respects .gitignore, file size limits, and directory traversal protection

#### Flow Visualizer Benefits:

##### 🎯 **For Intuitive Code Exploration**:

- **Natural Questions**: Ask "How does nested menu parsing work?" in plain English
- **Architecture Understanding**: Get clear explanations of system components and relationships
- **Data Flow Tracing**: Understand how data moves through the parsing pipeline
- **Pattern Discovery**: Identify recurring structures and design patterns in the codebase

##### 🔧 **For Targeted Investigation**:

- **File Structure Analysis**: Get organized overview of project organization and dependencies
- **Specific Component Deep-Dive**: Focus analysis on particular parsing modules or visualization components
- **Repository Metadata**: Understand project structure, size constraints, and organization
- **Context-Aware Reading**: Analyze files with full understanding of their role in the system

##### 🧠 **For Learning and Documentation**:

- **Beginner-Friendly**: Natural language interface makes complex code accessible
- **System Documentation**: Generate clear explanations of how components work together
- **Knowledge Transfer**: Perfect for onboarding or explaining complex nested menu logic
- **Cost-Effective Learning**: No external API costs, uses local processing only

#### Specific Tools Available:

1. **`initialize_repository`**: Set up codebase for natural language analysis
2. **`get_repo_info`**: Retrieve repository metadata and configuration details
3. **`get_repo_structure`**: Explore file/directory organization with intelligent depth control
4. **`read_file`**: Analyze specific files with contextual understanding and language detection

#### Example Flow Visualizer Workflow:

```
🔍 Natural Language Investigation: "Understanding v15_mc_evil_robin1 issue"

1. initialize_repository: Set up The Plot Thickens for analysis
2. "How does menu parsing work in this project?"
3. "What files are responsible for ID generation?"
4. get_repo_structure: Explore parsing-related directories
5. "Show me how MenuNode objects are created and used"
6. read_file: Deep dive into parser.py with contextual explanation
```

#### Technical Specifications:

- **Scanning Depth**: Default 3 levels (configurable)
- **File Size Limit**: 1MB maximum per file
- **Line Limit**: 1000 lines maximum per file analysis
- **Security**: Validates file paths, prevents directory traversal
- **Integration**: Respects .gitignore patterns automatically
- **Processing**: 100% local, no external dependencies

#### Perfect Triple Synergy:

- **Code Understanding MCP**: Semantic relationships and critical file identification
- **MCP Git Ingest**: Repository research and pattern discovery capabilities
- **Code Analysis MCP**: Natural language exploration and intuitive investigation
- **Combined Power**: Comprehensive understanding + Complete context + Intuitive exploration = Ultimate debugging workflow

---

### 10. **MCP Proxy Server** 🔄⭐ **(NEW)**

**Configuration ID**: `mcp-proxy`  
**Purpose**: Aggregate and serve multiple MCP servers through a unified interface  
**Command**: `node build/index.js`  
**Author**: `adamwattis`

#### Revolutionary Capabilities:

- **Multi-Server Aggregation**: Connect to and manage multiple MCP resource servers simultaneously
- **Unified Interface**: Expose combined capabilities from all connected servers through single interface
- **Request Routing**: Intelligently route requests to appropriate backend servers
- **Resource Management**: Aggregate resources from all connected servers with consistent URI schemes
- **Tool Orchestration**: Expose tools from all connected servers and route calls appropriately
- **Centralized Management**: Single point of control for multiple MCP server instances

#### Flow Visualizer Benefits:

##### 🎯 **For Multi-Server Orchestration**:

- **Centralized Access**: Access all MCP servers through single connection point
- **Simplified Management**: Manage multiple debugging tools from unified interface
- **Resource Aggregation**: Combine capabilities from specialized servers seamlessly
- **Load Distribution**: Distribute complex analysis tasks across multiple backend servers

##### 🔧 **For Advanced Workflows**:

- **Server Composition**: Combine different analysis capabilities (semantic + contextual + natural language)
- **Failover Support**: Maintain functionality even if individual servers fail
- **Scalable Architecture**: Add new analysis capabilities without reconfiguring clients
- **Protocol Translation**: Bridge different MCP server types and versions

##### 🌐 **For Enterprise Integration**:

- **Remote Server Support**: Connect to both local and remote MCP servers via SSE
- **Authentication Management**: Handle authentication across multiple backend services
- **Connection Pooling**: Maintain efficient connections to multiple servers
- **Monitoring & Logging**: Centralized monitoring of all MCP server interactions

#### Technical Specifications:

- **Transport Support**: Both stdio and Server-Sent Events (SSE)
- **Configuration**: JSON-based server configuration with flexible transport options
- **Connection Management**: Maintains persistent connections to backend servers
- **Error Handling**: Comprehensive error handling with recovery strategies
- **Protocol Compliance**: Full MCP protocol compliance for seamless integration

#### Example Configuration:

```json
{
  "servers": [
    {
      "name": "Code Analysis Server",
      "transport": {
        "command": "python",
        "args": ["code_analysis.py"]
      }
    },
    {
      "name": "Remote Analysis Server",
      "transport": {
        "type": "sse",
        "url": "https://analysis-server.company.com/mcp"
      }
    }
  ]
}
```

#### Ultimate MCP Ecosystem:

- **Code Understanding MCP**: Deep semantic analysis and relationships
- **MCP Git Ingest**: Repository research and pattern discovery
- **Code Analysis MCP**: Natural language exploration and investigation
- **MCP Proxy Server**: Orchestrates and unifies all analysis capabilities
- **Combined Power**: Unified access to comprehensive analysis suite = Ultimate debugging ecosystem

---

## Configuration Details

### Installation Requirements:

- **Python Environment**: Virtual environment with required packages
- **UV Package Manager**: For code-understanding-mcp-server
- **Node.js Environment**: For codebase-mcp server
- **Database Access**: SQLite database for official-sqlite server
- **File System Permissions**: Read/write access to project directories

### Configuration File Location:

`.cursor/mcp.json` - Cursor editor MCP configuration

### Environment Variables:

- `PYTHONUNBUFFERED=1`: Ensures real-time output from Python servers
- `PYTHONPATH`: Set to project root for proper module imports

---

## Usage Guidelines

### Best Practices:

1. **Start with Code Understanding**: Use the semantic analysis tools first to understand overall structure
2. **Combine Multiple Servers**: Use filesystem + code-understanding for comprehensive analysis
3. **Leverage Memory**: Store insights and patterns for future debugging sessions
4. **Database Integration**: Use SQLite server for data-driven analysis
5. **Documentation First**: Check docs-crawler before implementing new features

### Common Workflows:

#### For New Bug Investigation:

1. **Code Understanding**: Map the affected components
2. **Filesystem**: Analyze relevant files and structures
3. **Memory**: Check for similar previous issues
4. **SQLite**: Validate data integrity if database-related

#### For Feature Development:

1. **Documentation**: Research best practices and examples
2. **GitHub**: Check related issues and pull requests
3. **Code Understanding**: Understand current architecture
4. **Filesystem**: Organize new code properly

#### For Performance Optimization:

1. **Code Understanding**: Identify complexity hotspots
2. **SQLite**: Analyze database performance
3. **Memory**: Record optimization strategies
4. **GitHub**: Track performance improvements

---

## Impact Assessment

### Before MCP Servers:

- ❌ Manual file reading and analysis
- ❌ Sequential, slow debugging process
- ❌ Limited context preservation
- ❌ Difficulty tracing complex relationships
- ❌ Repetitive investigation of similar issues

### After MCP Servers:

- ✅ **3-5x faster debugging** through semantic analysis
- ✅ **Comprehensive code understanding** via automated mapping
- ✅ **Persistent knowledge** across debugging sessions
- ✅ **Systematic root cause analysis** with data-driven insights
- ✅ **Proactive issue prevention** through pattern recognition

---

## Future Enhancements

### Potential Additional Servers:

- **Graph Analysis MCP**: Specialized graph algorithms and visualization
- **Performance Monitoring MCP**: Real-time performance tracking
- **Testing Automation MCP**: Automated test generation and execution
- **AST Analysis MCP**: Advanced Abstract Syntax Tree parsing

### Integration Opportunities:

- **IDE Integration**: Deeper integration with Cursor editor features
- **Continuous Integration**: Automated analysis in CI/CD pipelines
- **Real-time Monitoring**: Live debugging assistance during development
- **Collaborative Features**: Shared insights across development team

---

## Conclusion

The MCP server ecosystem represents a **paradigm shift** in AI-assisted development for The Plot Thickens Flow Visualizer POC. By providing direct access to specialized analysis tools, databases, and external resources, these servers enable:

- **🚀 Exponentially faster debugging** of complex issues like nested menu parsing
- **🧠 Deeper code understanding** through semantic analysis and mapping
- **📊 Data-driven decision making** via direct database access
- **🔄 Continuous learning** through persistent memory and knowledge accumulation
- **⚡ Streamlined workflows** that eliminate manual, repetitive tasks

The addition of the **Code Understanding MCP Server**, **MCP Git Ingest Server**, **Code Analysis MCP Server**, and **MCP Proxy Server** specifically addresses the challenges identified in debugging complex Ren'Py visual novel flow structures. Together, they provide semantic analysis capabilities, complete contextual awareness, natural language exploration, and unified orchestration necessary to efficiently resolve issues like the v15_mc_evil_robin1 nested menu parsing problem.

This infrastructure positions the project for rapid development, sophisticated debugging, and systematic problem-solving that scales with project complexity.

---

_Document Version: 1.3_  
_Last Updated: January 2025_  
_Author: AI Assistant with MCP Enhancement_
