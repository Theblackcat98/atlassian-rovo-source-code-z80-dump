# ACLI Rovo Dev Binary Analysis

## Binary Classification
- **File Type**: Mach-O 64-bit executable arm64
- **Language**: Go (Golang) - evidenced by Go runtime symbols, garbage collector references, and Go-specific error messages
- **Target Architecture**: ARM64 (Apple Silicon)
- **Dependencies**: Standard macOS system libraries

## Rovo Functionality Overview

The `acli` binary is Atlassian's Command Line Interface with embedded **Rovo Dev** functionality - an AI coding agent system that integrates with MCP (Model Context Protocol) servers.

## Key Components

### 1. Authentication System
- OAuth2-based authentication with Atlassian services
- Token management and storage
- Multi-organization support

### 2. Rovo Dev AI Agent Architecture
The binary contains an embedded Python-based AI agent system:

```
lib/atlassian_cli_rovodev/
├── src/rovodev/
│   ├── modules/
│   │   ├── instructions/        # AI agent instructions
│   │   ├── analytics/          # Usage tracking and metrics
│   │   └── mcp_utils.py        # MCP protocol handling
│   ├── commands/
│   │   ├── run/                # Command execution
│   │   ├── serve/              # MCP server functionality  
│   │   └── mcp/                # MCP protocol commands
│   └── ui/                     # Terminal user interface
```

### 3. MCP (Model Context Protocol) Integration
- Full MCP 1.9.2 implementation
- Server/client architecture for AI model communication
- Tool execution and permission management

## Critical Strings and Configurations

### MCP Tool Calls and System Interactions
Based on the binary analysis, the Rovo system uses these key endpoints and configurations:

```
# Authentication Endpoints
https://auth.atlassian.com/authorize?audience=api.atlassian.com
/oauth/token
/accessible-resources

# API Endpoints
/api/v1/jira/issue/{issueIdOrKey}
/api/v1/jira/project/{projectIdOrKey}
/api/v1/admin/org/{orgId}/user
/feedback-collector-api/feedback

# Environment Variables
ATLASSIAN_ACCESS_TOKEN_URL
CODEBUILD_RESOLVED_SOURCE_VERSION
VERCEL_GIT_COMMIT_SHA
```

### AI Agent Instructions
The binary contains embedded instruction templates for various AI tasks:

1. **create_instruction.md** - Code creation guidance
2. **improve_documentation.md** - Documentation enhancement
3. **summarize_jira_issues.md** - Issue summarization
4. **local_code_review.md** - Code review automation
5. **increase_unit_test_coverage.md** - Test generation
6. **summarize_confluence_page.md** - Confluence integration

### System Prompts and Configuration
While specific system prompts weren't found in plaintext, the binary contains references to:

- **Prompt toolkit integration** for terminal UI
- **Session management** for AI conversations
- **Tool permission systems** for secure execution
- **Adaptive fallback model** handling
- **Analytics and usage tracking**

## Security Architecture

### Authentication Flow
```go
// Extracted authentication pattern
type RovodevAuth struct {
    Profile  *config.RovodevProfile
    Token    string
    Site     string
}

// Commands identified:
// acli rovodev auth login
// acli rovodev auth status  
// acli rovodev auth logout
```

### Permission Model
The system implements a permission-based tool execution model with:
- Tool permission management
- Session-based access control
- External API mapping and validation

## MCP Server Implementation

### Server Configuration
The binary contains a full MCP server implementation that can:
- Serve AI model requests
- Execute tools with proper permissions  
- Handle session management
- Provide analytics and monitoring

### Key MCP Components
```python
# Inferred from binary analysis
class MCPServer:
    def handle_tool_call(self, tool_name: str, parameters: dict)
    def validate_permissions(self, tool: str, user: str) 
    def execute_command(self, command: str, context: dict)
    def track_usage(self, event: AnalyticsEvent)
```

## Analytics and Telemetry

### Data Collection
The system collects extensive analytics:
- Command usage patterns
- Tool execution metrics  
- Session duration and frequency
- Error tracking and crash reporting
- Code modification metrics
- LLM interaction patterns

### Mappers Identified
- `command_mapper.py` - Command usage tracking
- `mcp_mapper.py` - MCP protocol analytics
- `session_mapper.py` - Session analytics
- `tool_mapper.py` - Tool usage tracking
- `code_modification_mapper.py` - Code change tracking
- `llm_error_mapper.py` - AI model error tracking

## Commands and Usage Patterns

### Core Rovo Commands
```bash
# Authentication
acli rovodev auth login
acli rovodev auth login --email "user@atlassian.com" --token < token.txt
acli rovodev auth status
acli rovodev auth logout

# Core functionality (inferred from binary)  
acli rovodev run [command]
acli rovodev serve  # MCP server mode
acli rovodev config
```

### Integration Points
- **Jira**: Issue management, work item tracking
- **Confluence**: Page summarization and content generation
- **Git**: Code analysis and review automation
- **Local development**: Code generation, testing, documentation

## Technical Implementation Details

### Go Runtime Integration
The binary uses Go's runtime for:
- Concurrent execution management
- Memory management and garbage collection
- Network I/O and HTTP client operations
- Cross-platform file system operations

### Python Integration  
The embedded Python components handle:
- AI model interactions
- MCP protocol implementation
- Terminal UI rendering
- Analytics processing

### Key Libraries
- **Cobra CLI framework** for command structure
- **Prompt toolkit** for interactive terminal UI
- **MCP 1.9.2** for AI model communication
- **OpenTelemetry** for observability

## Security Considerations

### Token Management
- OAuth2 tokens stored in configuration files
- Environment variable support for CI/CD
- Secure token refresh mechanisms

### Permission Model
- Tool execution requires explicit permissions
- Session-based access control
- External API access validation

### Data Privacy
- Extensive analytics collection
- Usage pattern tracking
- Potential code content analysis

## Deployment Architecture

The binary appears designed for:
- **Local development environments** - Direct CLI usage
- **CI/CD pipelines** - Automated code analysis and generation
- **MCP server deployments** - Centralized AI agent services
- **Multi-tenant organizations** - Enterprise Atlassian integrations

This analysis reveals that `acli` is a sophisticated AI-powered development tool that combines traditional CLI functionality with modern AI agent capabilities, specifically designed to integrate with Atlassian's ecosystem while providing extensible AI-powered development assistance.
