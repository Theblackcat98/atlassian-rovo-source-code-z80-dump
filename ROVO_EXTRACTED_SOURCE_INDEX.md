# ACLI Rovo Dev - Extracted Source Code Index

## Summary
Successfully extracted 100+ Python source files from the embedded archive in the `acli` binary. This represents the complete Rovo Dev AI agent implementation.

## Directory Structure

```
lib/atlassian_cli_rovodev/
├── src/rovodev/                      # Core Rovo implementation
│   ├── common/                       # Shared utilities and configuration
│   ├── commands/                     # CLI command handlers
│   ├── modules/                      # Core functionality modules
│   ├── ui/                          # Terminal user interface
│   └── rovodev_cli.py               # Main CLI entry point
├── tests/                           # Comprehensive test suite
│   ├── common/
│   ├── commands/
│   ├── modules/
│   └── ui/
├── distribution/                    # Packaging and distribution
└── hooks/                          # Runtime hooks
```

## Key Components

### 1. AI Agent Instructions (`lib/atlassian_cli_rovodev/src/rovodev/modules/instructions/`)
- `create_instruction.md` - Code creation guidance
- `improve_documentation.md` - Documentation enhancement prompts
- `summarize_jira_issues.md` - Issue summarization instructions
- `local_code_review.md` - Code review automation prompts
- `increase_unit_test_coverage.md` - Test generation instructions
- `summarize_confluence_page.md` - Confluence integration prompts
- `instructions.yml` - Instruction registry and configuration

### 2. Core Modules (`lib/atlassian_cli_rovodev/src/rovodev/modules/`)
- `mcp_utils.py` - Model Context Protocol implementation
- `sessions.py` - AI session management
- `memory.py` - Conversation memory and context
- `tool_permissions.py` - Security and permission management
- `adaptive_fallback_model.py` - AI model fallback handling
- `usage.py` - Usage tracking and analytics
- `models.py` - Data models and schemas

### 3. Analytics System (`lib/atlassian_cli_rovodev/src/rovodev/modules/analytics/`)
- `atlassian_client.py` - Atlassian API client
- `processor.py` - Analytics data processing
- `code_metrics.py` - Code analysis metrics
- `user_info.py` - User tracking and identification
- `mappers/` - Event mapping for various operations
  - `mcp.py` - MCP protocol analytics
  - `command.py` - Command usage tracking
  - `session.py` - Session analytics
  - `tool.py` - Tool usage tracking
  - `code_modification.py` - Code change tracking
  - `llm.py` - LLM interaction analytics

### 4. Commands (`lib/atlassian_cli_rovodev/src/rovodev/commands/`)
- `auth/` - Authentication handling
- `config/` - Configuration management
- `mcp/` - MCP server/client commands
- `log/` - Logging functionality
- `run/` - Command execution
- `serve/` - MCP server mode

### 5. User Interface (`lib/atlassian_cli_rovodev/src/rovodev/ui/`)
- `prompt_session.py` - Interactive terminal session
- `components/` - UI components
  - `user_input_panel.py` - User input handling
  - `session_menu_panel.py` - Session management UI
  - `user_menu_panel.py` - User menu interface
  - `token_display.py` - Token/credential display

### 6. Configuration System (`lib/atlassian_cli_rovodev/src/rovodev/common/`)
- `config.py` - Configuration management
- `config_model.py` - Configuration data models
- `dynamic_config.py` - Runtime configuration
- `agent.py` - AI agent configuration
- `exceptions.py` - Custom exceptions
- `banner.py` - CLI branding

## Key Insights from Source Analysis

### MCP (Model Context Protocol) Integration
The system extensively uses MCP for AI model communication, with dedicated utilities for:
- Server/client protocol handling
- Tool execution with permission controls
- Session state management
- Analytics tracking

### Security Architecture
- Permission-based tool execution
- Session isolation
- Token-based authentication
- User activity tracking

### Analytics & Telemetry
Comprehensive data collection including:
- Command usage patterns
- Tool execution metrics
- Code modification tracking
- AI model interaction analytics
- Session duration and patterns
- Error tracking and crash reporting

### AI Agent Instructions
The system contains sophisticated prompts for various development tasks:
- Code generation and creation
- Documentation improvement
- Code review automation
- Test generation
- Issue summarization
- Confluence page processing

## Next Steps
1. Examine individual files for detailed implementation
2. Analyze AI instruction prompts for system behavior
3. Review analytics collection for privacy implications
4. Study MCP protocol implementation
5. Investigate security and permission models

## Files Available for Analysis
All 100+ extracted Python files are now available in the `lib/atlassian_cli_rovodev/` directory for detailed examination.
