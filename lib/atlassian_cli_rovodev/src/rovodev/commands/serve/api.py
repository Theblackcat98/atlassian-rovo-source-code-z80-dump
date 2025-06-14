import asyncio
import json
from contextlib import asynccontextmanager
from typing import Annotated, Any, AsyncGenerator

import uvicorn
from fastapi import Depends, FastAPI, HTTPException
from fastapi.encoders import jsonable_encoder
from loguru import logger
from mcp.types import CallToolResult, TextContent
from pydantic import BaseModel
from pydantic_ai import Agent
from pydantic_ai._agent_graph import CallToolsNode
from pydantic_ai.messages import ModelMessage, ModelResponse, SystemPromptPart, ToolCallPart, ToolReturnPart
from pydantic_ai.tools import ToolDefinition
from pydantic_ai.usage import Usage, UsageLimits
from pydantic_graph import End
from sse_starlette.sse import EventSourceResponse

from nemo.agent import AgentFactory
from nemo.dependencies import AgentDeps
from nemo.utils import log_node

EventSourceResponse.media_type = "text/event-stream"


SSE_EXAMPLE = """\
----------------------- NON-STREAMING EXAMPLE -----------------------
event: user-prompt
data: {"content": "Open the README", "timestamp": "2025-06-06T23:16:23.639287+00:00", "part_kind": "user-prompt"}

event: text
data: {"content": "I'll open the README file for you.", "part_kind": "text"}

event: tool-call
data: {"tool_name": "open_files", "args": {"file_paths": ["README.md"]}, "tool_call_id": "toolu_vrtx_01Wh7sD8bFpbZfUMfPmGXmBv", "part_kind": "tool-call"}

event: tool-return
data: {"tool_name": "open_files", "content": "Successfully opened README.md:\n\n````markdown\n   0 # ACRA Python Monorepo\n````", "tool_call_id": "toolu_vrtx_01Q3Mri3FVDwnJybxzwb4aMb", "timestamp": "2025-06-06T23:00:06.062335+00:00", "part_kind": "tool-return"}

event: text
data: {"content": "The README file shows this is the ACRA  Python Monorepo", "part_kind": "text"}

----------------------- STREAMING EXAMPLE ---------------------------
event: user-prompt
data: {"content": "Open the README", "timestamp": "2025-06-06T23:00:02.794168+00:00", "part_kind": "user-prompt"}

event: part_start
data: {"index": 0, "part": {"content": "I'll open the README", "part_kind": "text"}, "event_kind": "part_start"}

event: part_delta
data: {"index": 0, "delta": {"content_delta": " file for you.", "part_delta_kind": "text"}, "event_kind": "part_delta"}

event: part_start
data: {"index": 1, "part": {"tool_name": "open_files", "args": null, "tool_call_id": "toolu_vrtx_01Q3Mri3FVDwnJybxzwb4aMb", "part_kind": "tool-call"}, "event_kind": "part_start"}

event: part_delta
data: {"index": 1, "delta": {"tool_name_delta": "", "args_delta": "", "tool_call_id": "toolu_vrtx_01Q3Mri3FVDwnJybxzwb4aMb", "part_delta_kind": "tool_call"}, "event_kind": "part_delta"}

event: part_delta
data: {"index": 1, "delta": {"tool_name_delta": "", "args_delta": "{\"file_paths\": [\"README.md\"]}", "tool_call_id": "toolu_vrtx_01Q3Mri3FVDwnJybxzwb4aMb", "part_delta_kind": "tool_call"}, "event_kind": "part_delta"}

event: tool-return
data: {"tool_name": "open_files", "content": "Successfully opened README.md:\n\n````markdown\n   0 # ACRA Python Monorepo\n````", "tool_call_id": "toolu_vrtx_01Q3Mri3FVDwnJybxzwb4aMb", "timestamp": "2025-06-06T23:00:06.062335+00:00", "part_kind": "tool-return"}

event: part_start
data: {"index": 0, "part": {"content": "The README file shows this is the ACRA", "part_kind": "text"}, "event_kind": "part_start"}

event: part_delta
data: {"index": 0, "delta": {"content_delta": " Python Monorepo", "part_delta_kind": "text"}, "event_kind": "part_delta"}

"""


class ResetResponse(BaseModel):
    """Response model for reset endpoint."""

    message: str


class ChatRequest(BaseModel):
    """Request model for chat endpoint."""

    message: str


class ToolRequest(BaseModel):
    """Request model for tool endpoint."""

    tool_name: str
    arguments: dict[str, Any]


class ToolResponse(BaseModel):
    """Response model for tool endpoint."""

    result: str


def normalize_tool_result(tool_content: Any) -> str:
    """Normalize the tool result to a string."""
    if isinstance(tool_content, CallToolResult):
        return "\n".join([chunk.text for chunk in tool_content.content if isinstance(chunk, TextContent)])
    return str(tool_content)


def get_server(
    agent: Agent[AgentDeps, str],
    agent_factory: AgentFactory,
    streaming: bool = False,
    initial_message: str | None = None,
) -> FastAPI:
    """Get the rovodev server object."""

    deps = AgentDeps(interactive=False, mcp_servers=agent._mcp_servers)  # type: ignore
    usage_limits = UsageLimits(request_limit=agent_factory.max_iterations)

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        """Lifespan handler to start MCP server(s)."""
        async with agent.run_mcp_servers():
            # Start initial chat if message is provided
            if initial_message:
                app_state_instance.initial_chat_task = asyncio.create_task(
                    run_initial_chat(initial_message, app_state_instance)
                )
            yield

    app = FastAPI(title="Rovo Dev serve app", version="2", lifespan=lifespan)

    class AppState:
        def __init__(self) -> None:
            self.message_history: list[ModelMessage] = []
            self.usage = Usage()
            self.conversation_buffer: list[dict[str, str]] = []  # Stores entire conversation for replay
            self.initial_chat_complete: bool = False
            self.initial_chat_task: asyncio.Task | None = None
            self.chat_in_progress: bool = False  # Track if a chat is currently running
            self.chat_lock: asyncio.Lock = asyncio.Lock()  # Prevent concurrent chats

    # Singleton instance of AppState
    app_state_instance = AppState()

    # Dependency that returns the singleton instance
    def get_app_state():
        return app_state_instance

    async def chat_generator(message: str, state: AppState) -> AsyncGenerator[dict[str, str], Any]:
        """Generator to stream chat responses."""
        async with agent.iter(
            message, message_history=state.message_history, usage=state.usage, usage_limits=usage_limits, deps=deps
        ) as agent_run:
            async for node in agent_run:
                log_node(node, agent_factory.name)
                if agent.is_model_request_node(node):
                    for part in node.request.parts:
                        if isinstance(part, SystemPromptPart):
                            continue
                        event = {"event": part.part_kind, "data": json.dumps(jsonable_encoder(part))}
                        state.conversation_buffer.append(event)
                        yield event
                    if streaming:
                        async with node.stream(agent_run.ctx) as request_stream:
                            async for stream_event in request_stream:
                                if stream_event.event_kind == "final_result":
                                    continue
                                event = {
                                    "event": stream_event.event_kind,
                                    "data": json.dumps(jsonable_encoder(stream_event)),
                                }
                                state.conversation_buffer.append(event)
                                yield event
                elif Agent.is_call_tools_node(node) and not streaming:
                    for part in node.model_response.parts:
                        event = {"event": part.part_kind, "data": json.dumps(jsonable_encoder(part))}
                        state.conversation_buffer.append(event)
                        yield event
        if agent_run.result:
            state.message_history.extend(agent_run.result.new_messages())
            state.usage = agent_run.result.usage()

    async def run_initial_chat(message: str, state: AppState) -> None:
        """Run the initial chat and buffer the events."""
        try:
            state.chat_in_progress = True
            async for event in chat_generator(message, state):
                pass
        except Exception as e:
            # Log the error but don't crash the server
            logger.error(f"Error in initial chat: {e}")
        finally:
            state.initial_chat_complete = True
            state.chat_in_progress = False

    async def chat_with_concurrency_check(message: str, state: AppState) -> AsyncGenerator[dict[str, str], Any]:
        """Generator for chat endpoint that handles concurrency and conversation buffering."""
        # Check if a chat is already in progress
        if state.chat_in_progress:
            raise HTTPException(status_code=409, detail="Chat already in progress")

        try:
            async with state.chat_lock:
                state.chat_in_progress = True
                async for event in chat_generator(message, state):
                    yield event
        finally:
            state.chat_in_progress = False

    async def replay_generator(state: AppState) -> AsyncGenerator[dict[str, str], Any]:
        """Generator to replay buffered events and continue with new ones."""
        # First, yield all buffered events from the conversation
        for event in state.conversation_buffer:
            yield event

        # If there's a chat in progress (initial or concurrent), continue streaming new events
        if state.chat_in_progress:
            # Continue yielding events as they come in
            buffer_index = len(state.conversation_buffer)
            while state.chat_in_progress:
                await asyncio.sleep(0.01)  # Small delay to avoid busy waiting
                # Yield any new events that have been added to the buffer
                while buffer_index < len(state.conversation_buffer):
                    yield state.conversation_buffer[buffer_index]
                    buffer_index += 1

    @app.post("/v2/reset")
    async def reset(state: Annotated[AppState, Depends(get_app_state)]) -> ResetResponse:
        """Reset the agent history and MCP servers."""
        state.message_history = []
        state.usage = Usage()
        state.conversation_buffer = []
        state.initial_chat_complete = False
        state.chat_in_progress = False
        if state.initial_chat_task:
            state.initial_chat_task.cancel()
            state.initial_chat_task = None
        return ResetResponse(message="Agent reset")

    @app.post(
        "/v2/chat",
        response_class=EventSourceResponse,
        responses={"200": {"content": {"text/event-stream": {"example": SSE_EXAMPLE}}}},
    )
    async def chat(request: ChatRequest, state: Annotated[AppState, Depends(get_app_state)]):
        """Chat endpoint."""
        # Check if a chat is already in progress
        if state.chat_in_progress:
            raise HTTPException(status_code=409, detail="Chat already in progress")

        try:
            async with state.chat_lock:
                state.chat_in_progress = True
                return EventSourceResponse(chat_generator(request.message, state), sep="\n")
        finally:
            state.chat_in_progress = False

    @app.post(
        "/v2/replay",
        response_class=EventSourceResponse,
        responses={"200": {"content": {"text/event-stream": {"example": SSE_EXAMPLE}}}},
    )
    async def replay(state: Annotated[AppState, Depends(get_app_state)]):
        """Replay endpoint to stream buffered chat events and continue streaming new ones."""
        return EventSourceResponse(replay_generator(state), sep="\n")

    @app.get("/v2/tools", response_model=list[ToolDefinition])
    async def tools() -> list[ToolDefinition]:
        """Get the list of available tools."""
        mcp_tools = [tool_def for server in agent._mcp_servers for tool_def in await server.list_tools()]
        function_tools = [
            ToolDefinition(
                name=tool.name,
                description=tool.description,
                parameters_json_schema=tool._base_parameters_json_schema,
                strict=tool.strict,
            )
            for tool in agent._function_tools.values()
        ]
        return mcp_tools + function_tools

    @app.post("/v2/tool", response_model=ToolResponse)
    async def tool(request: ToolRequest, state: Annotated[AppState, Depends(get_app_state)]) -> ToolResponse:
        """Tool endpoint."""
        async with agent.iter(
            None, message_history=state.message_history, usage=state.usage, usage_limits=usage_limits, deps=deps
        ) as agent_run:
            call_tools_node: CallToolsNode = CallToolsNode(
                model_response=ModelResponse(parts=[ToolCallPart(tool_name=request.tool_name, args=request.arguments)]),
            )
            result = await call_tools_node.run(agent_run.ctx)
            if isinstance(result, End) or not isinstance(result.request.parts[0], ToolReturnPart):
                raise ValueError("Tool call failed")
            return ToolResponse(result=normalize_tool_result(result.request.parts[0].content))

    @app.get("/healthcheck")
    async def healthcheck():
        """Health check endpoint."""
        return {"status": "healthy"}

    return app


def start_server(
    agent: Agent[AgentDeps, str],
    agent_factory: AgentFactory,
    port: int,
    streaming: bool = False,
    initial_message: str | None = None,
) -> None:
    """Start the FastAPI server."""
    app = get_server(agent, agent_factory, streaming, initial_message)
    config = uvicorn.Config(app, host="0.0.0.0", port=port, log_level="info", access_log=False, loop="asyncio")
    server = uvicorn.Server(config)

    try:
        logger.info(f"Starting server on http://0.0.0.0:{port}")
        asyncio.run(asyncio.gather(server.serve()))  # type: ignore
    except asyncio.CancelledError:
        logger.info("Server task was cancelled")
    finally:
        logger.info("Server shutdown complete")
