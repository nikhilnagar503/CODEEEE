from __future__ import annotations
from typing import AsyncGenerator
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

            messages = self.context_manager.get_messages()
            response_text  = ""

            async for event in self.client.chat_completion(self.context_manager.get_messages(),stream=True):
                if event.event_type == StreamEventType.TEXT_DELTA:
                    content=event.text_delta.content if event.text_delta else None
                    
                    response_text += content or ""
                    
                    yield AgentEvent.text_delta(content)
                    
                elif event.event_type == StreamEventType.ERROR:
                    yield AgentEvent.agent_error(error=event.error or "Unknown error Occurred")
            
            
            
            self.context_manager.add_Assistant_message(response_text or "")
                    
            if response_text :
                yield AgentEvent.text_complete(content=response_text)
                
            
        
    async def __aenter__(self) -> Agent :
        return self 

    async def __aexit__(self, exc_type, exc_value, exc_tb) -> None :
        if self.client:
            await self.client.close()
            self.client = None 