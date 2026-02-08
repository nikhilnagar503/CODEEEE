from __future__ import annotations
from typing import AsyncGenerator
from pathlib import Path
import json
from Tool.registry import create_default_registry
from client.response import StreamEventType

from click import prompt

from agent.events import AgentEvent, AgentEventType
import client
from client.llm_client import llm_client
from context.manager import context_manager
        

class Agent :
    def __init__(self):
        self.client = llm_client()
        self.context_manager = context_manager()
        self.tool_registry = create_default_registry()
        
    async def  run(self, message:str):
        
        yield AgentEvent.agent_start(message=message)
        self.context_manager.add_user_message(message)
        
        #  add the user message for context 
        
        final_response = ""
        async for event in self._agentic_loop():
            yield event 
            
            if event.type == AgentEventType.TEXT_COMPLETE :
                final_response  = event.data.get("content", "")
        
        yield AgentEvent.agent_end(final_response)
        
        
        
        
        
    async def  _agentic_loop(self)-> AsyncGenerator[AgentEvent , None ]:

            tool_schema = self.tool_registry.get_schemas()
            max_steps = 5

            for _ in range(max_steps):
                messages = self.context_manager.get_messages()
                response_text = ""
                use_tools = bool(tool_schema)

                if use_tools:
                    event = None
                    async for ev in self.client.chat_completion(
                        messages,
                        tools=tool_schema,
                        stream=False,
                    ):
                        event = ev

                    if event is None:
                        return

                    if event.event_type == StreamEventType.ERROR:
                        yield AgentEvent.agent_error(error=event.error or "Unknown error Occurred")
                        return

                    if event.tool_calls:
                        self.context_manager.add_Assistant_message(
                            content=event.text_delta.content if event.text_delta else "",
                            extra={"tool_calls": event.tool_calls},
                        )

                        for call in event.tool_calls:
                            function_data = call.get("function", {})
                            name = function_data.get("name")
                            args_text = function_data.get("arguments", "{}") or "{}"
                            try:
                                args = json.loads(args_text)
                            except json.JSONDecodeError:
                                args = {}

                            if not name:
                                self.context_manager.add_tool_message(
                                    call.get("id", ""),
                                    "Tool call missing name",
                                )
                                continue

                            result = await self.tool_registry.invoke(
                                name,
                                args,
                                Path.cwd(),
                            )
                            content = result.output if result.success else (result.error or "")
                            self.context_manager.add_tool_message(call.get("id", ""), content)

                        continue

                    if event.text_delta and event.text_delta.content:
                        response_text = event.text_delta.content

                    self.context_manager.add_Assistant_message(response_text or "")
                    if response_text:
                        yield AgentEvent.text_complete(content=response_text)
                    return

                async for event in self.client.chat_completion(
                    messages,
                    tools=None,
                    stream=True,
                ):
                    if event.event_type == StreamEventType.TEXT_DELTA:
                        content = event.text_delta.content if event.text_delta else None
                        response_text += content or ""
                        yield AgentEvent.text_delta(content)
                    elif event.event_type == StreamEventType.ERROR:
                        yield AgentEvent.agent_error(error=event.error or "Unknown error Occurred")
                        return

                self.context_manager.add_Assistant_message(response_text or "")
                if response_text:
                    yield AgentEvent.text_complete(content=response_text)
                return

            yield AgentEvent.agent_error(error="Tool loop exceeded maximum steps")
        
    async def __aenter__(self) -> Agent :
        return self 

    async def __aexit__(self, exc_type, exc_value, exc_tb) -> None :
        if self.client:
            await self.client.close()
            self.client = None 