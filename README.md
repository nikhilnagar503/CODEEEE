# AI Coding Agent - Architecture & Implementation Guide

## Table of Contents
1. [Overview](#overview)
2. [Core Architecture](#core-architecture)
3. [Component Details](#component-details)
4. [Tool System](#tool-system)
5. [Configuration](#configuration)
6. [Session Management](#session-management)
7. [Safety & Approval System](#safety--approval-system)
8. [Context Management](#context-management)
9. [Advanced Features](#advanced-features)
10. [Usage Examples](#usage-examples)

---

## Overview

This is an AI coding agent built to autonomously operate on real codebases. It can read, write, edit files, execute shell commands, search the web, and maintain conversational memory across sessions.

### Key Capabilities
- **File Operations**: Read, write, edit files with diff generation
- **Shell Execution**: Run commands with safety checks and approval flows
- **Web Access**: Search and fetch web content
- **Code Search**: Grep and glob pattern matching
- **Memory**: Persistent user preferences and session state
- **Task Management**: Track multi-step tasks with todos
- **MCP Integration**: Connect to Model Context Protocol servers
- **Sub-agents**: Spawn isolated agents for complex tasks

---

## Core Architecture

### High-Level Flow

```
User Input → Agent → LLM Client → Tool Registry → Tool Execution → Response
     ↑                    ↓                                            |
     └────────────── Context Manager ←──────────────────────────────┘
```

### Main Components

1. **Agent** (`agent/agent.py`)
   - Orchestrates the main agentic loop
   - Manages turn-based conversation flow
   - Handles tool call execution
   - Implements loop detection and context compression

2. **Session** (`agent/session.py`)
   - Maintains session state (ID, timestamps, turn count)
   - Creates and manages all subsystems
   - Handles initialization of tools, MCP servers, hooks

3. **LLM Client** (`client/llm_client.py`)
   - Interfaces with OpenAI-compatible APIs
   - Handles streaming responses
   - Manages tool call parsing
   - Implements retry logic with exponential backoff

4. **Context Manager** (`context/manager.py`)
   - Manages conversation history
   - Tracks token usage
   - Implements context pruning and compression
   - Maintains system prompts

5. **Tool Registry** (`tools/registry.py`)
   - Registers and manages available tools
   - Validates tool parameters
   - Routes tool invocations
   - Handles approval workflow integration

---

## Component Details

### Agent Loop (`agent/agent.py`)

The agent runs in a turn-based loop with the following steps:

```python
async def _agentic_loop(self):
    for turn_num in range(max_turns):
        # 1. Check context size, compress if needed
        if self.session.context_manager.needs_compression():
            summary = await self.session.chat_compactor.compress()
            self.session.context_manager.replace_with_summary(summary)
        
        # 2. Get tool schemas and build messages
        tool_schemas = self.session.tool_registry.get_schemas()
        messages = self.session.context_manager.get_messages()
        
        # 3. Stream LLM response
        async for event in self.session.client.chat_completion(messages, tools):
            # Handle text deltas, tool calls, errors
            
        # 4. Execute tool calls
        for tool_call in tool_calls:
            result = await self.session.tool_registry.invoke(tool_call)
            
        # 5. Check for loops
        if self.session.loop_detector.check_for_loop():
            # Add loop-breaking prompt
            
        # 6. Return if no more tool calls
        if not tool_calls:
            return
```

**Key Features:**
- **Context Compression**: Automatically summarizes history when approaching token limits
- **Loop Detection**: Detects repetitive patterns and injects corrective prompts
- **Tool Call Validation**: Stops execution if tools fail parameter validation
- **Parallel Tool Execution**: Tools are invoked sequentially but LLM can request multiple in one turn

### Session Management (`agent/session.py`)

Sessions encapsulate all state for a conversation:

```python
class Session:
    def __init__(self, config: Config):
        self.session_id = str(uuid.uuid4())
        self.client = LLMClient(config)
        self.tool_registry = create_default_registry(config)
        self.context_manager = ContextManager(config, tools)
        self.mcp_manager = MCPManager(config)
        self.approval_manager = ApprovalManager(config.approval)
        self.loop_detector = LoopDetector()
        self.hook_system = HookSystem(config)
        # ... more state
```

**Responsibilities:**
- Initialize all subsystems
- Load user memory from disk
- Connect to MCP servers
- Discover custom tools
- Track session statistics

### LLM Client (`client/llm_client.py`)

Handles communication with OpenAI-compatible APIs:

```python
class LLMClient:
    async def chat_completion(self, messages, tools, stream=True):
        # Build request with tools
        kwargs = {
            "model": self.config.model_name,
            "messages": messages,
            "stream": stream,
        }
        if tools:
            kwargs["tools"] = self._build_tools(tools)
            kwargs["tool_choice"] = "auto"
        
        # Stream response with retry logic
        for attempt in range(self._max_retries):
            try:
                async for event in self._stream_response(client, kwargs):
                    yield event
            except RateLimitError:
                await asyncio.sleep(2**attempt)
```

**Features:**
- Streaming text deltas
- Tool call parsing and aggregation
- Token usage tracking
- Automatic retry on rate limits and connection errors

### Context Manager (`context/manager.py`)

Manages conversation history and token budget:

```python
class ContextManager:
    def __init__(self, config, user_memory, tools):
        self._system_prompt = get_system_prompt(config, user_memory, tools)
        self._messages: list[MessageItem] = []
        self.total_usage = TokenUsage()
    
    def add_user_message(self, content: str):
        # Create MessageItem with token count
        
    def needs_compression(self) -> bool:
        # Check if we're at 80% of context window
        return current_tokens > (context_limit * 0.8)
    
    def prune_tool_outputs(self):
        # Clear old tool results to save tokens
```

**Key Concepts:**
- **Message Items**: Structured conversation turns with metadata
- **Token Counting**: Uses tiktoken to estimate token usage
- **Pruning**: Removes old tool outputs while protecting recent ones
- **Compression**: Replaces entire history with a summary when needed

---

## Tool System

### Tool Base Class (`tools/base.py`)

All tools inherit from the `Tool` base class:

```python
class Tool(abc.ABC):
    name: str = "base_tool"
    description: str = "Base tool"
    kind: ToolKind = ToolKind.READ
    
    @property
    def schema(self) -> dict | type[BaseModel]:
        # Define parameters using Pydantic model
        
    @abc.abstractmethod
    async def execute(self, invocation: ToolInvocation) -> ToolResult:
        # Implement tool logic
        
    def validate_params(self, params: dict) -> list[str]:
        # Validate using Pydantic schema
        
    async def get_confirmation(self, invocation) -> ToolConfirmation | None:
        # Return confirmation details for approval
```

### Built-in Tools (`tools/builtin/`)

#### Read File (`read_file.py`)
- Reads text files with line numbers
- Supports offset/limit for large files
- Detects and rejects binary files
- Syntax highlighting in CLI output

#### Write File (`write_file.py`)
- Creates new files or overwrites existing ones
- Auto-creates parent directories
- Shows diff preview in approval flow
- Tracks file changes with FileDiff

#### Edit File (`edit_file.py`)
- Precise search/replace edits
- Validates exact string matches
- Supports replace-all mode
- Shows helpful error messages on mismatch

#### Shell (`shell.py`)
- Executes shell commands with timeout
- Blocks dangerous commands (rm -rf /, etc.)
- Filters environment variables
- Captures stdout/stderr separately

#### List Dir (`list_dir.py`)
- Lists directory contents
- Sorts folders first, then files
- Optional hidden file inclusion

#### Grep (`grep.py`)
- Regex search in file contents
- Case-insensitive option
- Skips binary files and common excludes
- Shows file path and line numbers

#### Glob (`glob.py`)
- Pattern-based file finding
- Supports ** for recursive matching
- Returns relative paths

#### Web Search (`web_search.py`)
- DuckDuckGo search via ddgs library
- Returns titles, URLs, snippets
- Configurable result count

#### Web Fetch (`web_fetch.py`)
- HTTP GET requests
- Follows redirects
- Configurable timeout
- Returns response body as text

#### Memory (`memory.py`)
- Persistent key-value storage
- Actions: set, get, delete, list, clear
- Stored in user data directory
- Survives sessions

#### Todos (`todo.py`)
- In-session task tracking
- Actions: add, complete, list, clear
- UUID-based task IDs
- Not persisted across sessions

### Tool Registry (`tools/registry.py`)

Central registry for all tools:

```python
class ToolRegistry:
    def register(self, tool: Tool):
        # Add tool to registry
        
    def get_schemas(self) -> list[dict]:
        # Return OpenAI function schemas
        
    async def invoke(self, name, params, cwd, hooks, approval):
        # 1. Get tool from registry
        # 2. Validate parameters
        # 3. Run hooks (before_tool)
        # 4. Check approval if needed
        # 5. Execute tool
        # 6. Run hooks (after_tool)
        return result
```

### Tool Discovery (`tools/discovery.py`)

Automatically loads custom tools from:
- `{project}/.ai-agent/tools/*.py`
- `{user_config}/.ai-agent/tools/*.py`

```python
class ToolDiscoveryManager:
    def discover_all(self):
        # Scan directories for .py files
        # Dynamically import modules
        # Find Tool subclasses
        # Register with registry
```

### MCP Tools (`tools/mcp/`)

Model Context Protocol integration:

```python
class MCPManager:
    async def initialize(self):
        # Connect to configured MCP servers (stdio or HTTP)
        
    def register_tools(self, registry: ToolRegistry):
        # Wrap MCP tools as Tool instances
        # Register with main registry
```

---

## Configuration

### Config Structure (`config/config.py`)

```python
class Config(BaseModel):
    model: ModelConfig  # name, temperature, context_window
    cwd: Path  # Working directory
    shell_environment: ShellEnvironmentPolicy  # Env var filtering
    hooks_enabled: bool
    hooks: list[HookConfig]
    approval: ApprovalPolicy  # on-request, auto, never, etc.
    max_turns: int  # Safety limit
    mcp_servers: dict[str, MCPServerConfig]
    allowed_tools: list[str] | None  # Whitelist
    developer_instructions: str | None  # From AGENT.MD
    user_instructions: str | None
    debug: bool
```

### Config Loading (`config/loader.py`)

Hierarchical config merging:

1. System config: `~/.config/ai-agent/config.toml`
2. Project config: `{project}/.ai-agent/config.toml`
3. Environment variables: `MODEL`, `OPENAI_API_KEY`, `BASE_URL`
4. AGENT.MD file content → developer_instructions

```python
def load_config(cwd: Path | None) -> Config:
    # 1. Load system config
    # 2. Load project config and merge
    # 3. Apply environment overrides
    # 4. Load AGENT.MD if present
    # 5. Validate and return
```

### Approval Policies

- **on-request**: Prompt user for all mutating operations
- **on-failure**: Only prompt if command previously failed
- **auto**: Allow all operations automatically
- **auto-edit**: Auto-approve edits, prompt for shell commands
- **never**: Block all mutating operations
- **yolo**: Allow everything (dangerous)

---

## Session Management

### Persistence (`agent/persistence.py`)

Save/restore conversation state:

```python
@dataclass
class SessionSnapshot:
    session_id: str
    created_at: datetime
    updated_at: datetime
    turn_count: int
    messages: list[dict]
    total_usage: TokenUsage

class PersistenceManager:
    def save_session(self, snapshot: SessionSnapshot):
        # Save to ~/.local/share/ai-agent/sessions/{id}.json
        
    def load_session(self, session_id: str) -> SessionSnapshot:
        # Load from disk
        
    def save_checkpoint(self, snapshot) -> str:
        # Save with timestamp in name
        
    def load_checkpoint(self, checkpoint_id: str) -> SessionSnapshot:
        # Load specific checkpoint
```

**Commands:**
- `/save` - Save current session
- `/sessions` - List saved sessions
- `/resume <id>` - Restore a session
- `/checkpoint` - Create named checkpoint
- `/restore <checkpoint_id>` - Restore checkpoint

---

## Safety & Approval System

### Approval Manager (`safety/approval.py`)

```python
class ApprovalManager:
    async def check_approval(self, context: ApprovalContext) -> ApprovalDecision:
        # Based on policy, decide: AUTO_APPROVED, NEEDS_CONFIRMATION, REJECTED
        
    def request_confirmation(self, confirmation: ToolConfirmation) -> bool:
        # Show diff/command to user via callback
        # Return user's decision
```

### Approval Flow

1. Tool prepares `ToolConfirmation` with details
2. `ApprovalManager.check_approval()` evaluates policy
3. If NEEDS_CONFIRMATION, show TUI prompt with diff
4. User approves (y/n)
5. Tool executes only if approved

### Hook System (`hooks/hook_system.py`)

Run scripts at lifecycle events:

```python
class HookSystem:
    async def trigger_before_agent(self, message: str):
        # Run hooks configured for "before_agent"
        
    async def trigger_after_tool(self, name, params, result):
        # Run hooks for "after_tool"
```

**Hook Triggers:**
- `before_agent` - Before processing user message
- `after_agent` - After generating response
- `before_tool` - Before tool execution
- `after_tool` - After tool execution
- `on_error` - On any error

**Use Cases:**
- Run tests before commits
- Log all tool calls
- Validate changes
- Send notifications

---

## Context Management

### Compaction (`context/compaction.py`)

When context grows too large:

```python
class ChatCompactor:
    async def compress(self, context_manager) -> tuple[str, TokenUsage]:
        # 1. Build special compression prompt
        # 2. Send full history to LLM
        # 3. Request structured summary
        # 4. Return summary + token usage
```

Summary structure:
- Original goal
- Completed actions (DO NOT REPEAT)
- Current state
- Remaining tasks
- Next step
- Key context

### Loop Detection (`context/loop_detector.py`)

Tracks recent actions to detect loops:

```python
class LoopDetector:
    def record_action(self, action_type, **kwargs):
        # Add to recent actions ring buffer
        
    def check_for_loop(self) -> str | None:
        # Detect: same tool + params repeated 3+ times
        # Return error description if loop found
```

When loop detected, agent injects a system prompt asking it to:
1. Stop and reflect
2. Consider different approach
3. Explain if task is impossible

---

## Advanced Features

### Sub-agents (`tools/subagents.py`)

Spawn isolated agents for focused tasks:

```python
class SubagentTool(Tool):
    async def execute(self, invocation: ToolInvocation):
        # 1. Create isolated config
        # 2. Build focused system prompt
        # 3. Run agent with limited tools
        # 4. Return final result
```

**Use Cases:**
- Complex codebase exploration
- Code review
- Test generation
- Refactoring planning

### TUI (`ui/tui.py`)

Rich terminal interface using `rich` library:

```python
class TUI:
    def tool_call_start(self, call_id, name, kind, arguments):
        # Show tool panel with args
        
    def tool_call_complete(self, call_id, name, result):
        # Show result with syntax highlighting
        # Display diffs for file changes
        # Format shell output
```

**Features:**
- Syntax highlighting for code
- Unified diff display
- Color-coded tool types
- Streaming assistant responses
- Approval prompts with diffs

### Events System (`agent/events.py`)

Type-safe event stream for UI integration:

```python
@dataclass
class AgentEvent:
    type: AgentEventType
    data: dict[str, Any]
    
    @classmethod
    def text_delta(cls, content: str):
        # Streaming text chunk
        
    @classmethod
    def tool_call_complete(cls, call_id, name, result):
        # Tool execution finished
```

**Event Types:**
- `AGENT_START` / `AGENT_END`
- `TEXT_DELTA` / `TEXT_COMPLETE`
- `TOOL_CALL_START` / `TOOL_CALL_COMPLETE`
- `AGENT_ERROR`

---

## Usage Examples

### Basic Usage

```bash
# Interactive mode
python main.py

# Single prompt mode
python main.py "create a hello world script"
```

### Commands

```bash
/help        # Show help
/config      # Show configuration
/tools       # List available tools
/mcp         # Show MCP server status
/stats       # Session statistics

/model <name>      # Switch model
/approval <mode>   # Change approval policy

/save              # Save session
/sessions          # List sessions
/resume <id>       # Resume session

/checkpoint        # Create checkpoint
/restore <id>      # Restore checkpoint

/clear             # Clear conversation
/exit              # Quit
```

### Example Workflows

**File Creation:**
```
> Create a file utils/helpers.py with a function to format dates
```

**Code Editing:**
```
> In src/main.py, change the port from 8000 to 3000
```

**Running Tests:**
```
> Run the test suite and fix any failures
```

**Code Search:**
```
> Find all functions that use the database connection
```

**Web Research:**
```
> Search for best practices for Python async error handling
```

**Task Tracking:**
```
> Add a todo to refactor the auth module
> Mark todo abc123 as complete
> List all todos
```

### Configuration Example

`.ai-agent/config.toml`:
```toml
[model]
name = "gpt-4o-mini"
temperature = 0.7

approval = "on-request"
max_turns = 50

[mcp_servers.filesystem]
command = "npx"
args = ["-y", "@modelcontextprotocol/server-filesystem", "/path/to/project"]

[[hooks]]
name = "run-tests"
trigger = "after_tool"
command = "pytest"
enabled = true
```

---

## Environment Variables

- `OPENAI_API_KEY` / `API_KEY` - API key for OpenAI-compatible API
- `BASE_URL` - API base URL (default: OpenAI)
- `MODEL` - Model name override

---

## Directory Structure

```
.
├── agent/              # Core agent logic
│   ├── agent.py       # Main agentic loop
│   ├── events.py      # Event types
│   ├── session.py     # Session management
│   └── persistence.py # Save/restore
├── client/            # LLM client
│   ├── llm_client.py  # OpenAI-compatible client
│   └── response.py    # Response types
├── config/            # Configuration
│   ├── config.py      # Config models
│   └── loader.py      # Config loading
├── context/           # Context management
│   ├── manager.py     # Message history
│   ├── compaction.py  # Context compression
│   └── loop_detector.py # Loop detection
├── hooks/             # Hook system
│   └── hook_system.py
├── prompts/           # System prompts
│   └── system.py
├── safety/            # Safety & approval
│   └── approval.py
├── tools/             # Tool system
│   ├── base.py        # Base tool class
│   ├── registry.py    # Tool registry
│   ├── discovery.py   # Custom tool loader
│   ├── subagents.py   # Sub-agent tool
│   ├── builtin/       # Built-in tools
│   └── mcp/           # MCP integration
├── ui/                # User interface
│   └── tui.py         # Rich TUI
├── utils/             # Utilities
│   ├── errors.py
│   ├── paths.py
│   └── text.py
├── main.py            # Entry point
├── .env               # Environment config
└── requirements.txt   # Python dependencies
```

---

## Dependencies

Core:
- `openai` - LLM client
- `pydantic` - Config validation
- `click` - CLI framework
- `rich` - Terminal UI
- `tiktoken` - Token counting
- `python-dotenv` - .env loading

Tools:
- `httpx` - HTTP requests
- `ddgs` - DuckDuckGo search
- `fastmcp` - MCP client

Config:
- `tomli` - TOML parsing
- `platformdirs` - Cross-platform paths

---

## Key Design Decisions

1. **OpenAI Compatible**: Works with any OpenAI-compatible API
2. **Streaming First**: All text output streams for better UX
3. **Safety by Default**: Approval system prevents dangerous operations
4. **Extensible**: Custom tools, MCP servers, hooks
5. **Persistent**: Sessions and memory survive restarts
6. **Autonomous**: Runs to completion before returning to user
7. **Token Aware**: Compresses context to stay within limits
8. **Loop Detection**: Prevents infinite tool call loops

---

## Future Enhancements

Potential improvements:
- Parallel tool execution
- Tool call caching
- Vector-based code search
- Git integration tool
- Multi-agent collaboration
- Streaming tool results
- Voice input/output
- Browser automation tool
- Database query tool
- API testing tool

---

## Troubleshooting

**Agent loops on tool calls:**
- Check loop detector is working
- Review system prompt for clarity
- Use `/clear` to reset context

**Context overflow:**
- Reduce `max_turns`
- Enable context compression
- Use smaller model with larger context window

**MCP connection fails:**
- Check server command
- Verify environment variables
- Review server logs

**Tool validation errors:**
- Check parameter schema
- Ensure required fields provided
- Review tool documentation

---

## Contributing

To add a new tool:

1. Create `tools/builtin/my_tool.py`:
```python
class MyTool(Tool):
    name = "my_tool"
    description = "What it does"
    kind = ToolKind.READ
    
    schema = MyToolParams  # Pydantic model
    
    async def execute(self, invocation):
        # Implementation
        return ToolResult.success_result("Done")
```

2. Register in `tools/builtin/__init__.py`:
```python
from tools.builtin.my_tool import MyTool

def get_all_builtin_tools():
    return [MyTool, ...]
```

3. Add tests and documentation

---

## License & Credits

Built with:
- OpenAI API
- Rich library by Will McGugan
- Pydantic validation
- MCP by Anthropic

---

*Last Updated: February 18, 2026*
