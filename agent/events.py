from __future__ import annotations
from email import message
from enum import Enum
from dataclasses import dataclass, field
from client.response import TokenUsage
from typing import Any



class AgentEventType(str, Enum):
    # agent lifecycle events
    AGENT_STARTED = "agent_started"
    AGENT_FINISHED = "agent_finished"
    AGENT_ERROR = "agent_error"
    
    # task streaming events 
    TEXT_DELTA = "text_delta"
    TEXT_COMPLETE = "text_complete"
    
    
    
@dataclass
class AgentEvent:
    type : AgentEventType
    data : dict[str,Any] = field(default_factory=dict)
    @classmethod
    def agent_start(cls,message:str)-> AgentEvent :
        return cls(
            type=AgentEventType.AGENT_STARTED,
            data={"message":message},
            
        )
    @classmethod
    def agent_end(cls,repsonse:str|None = None , usage : TokenUsage|None = None )-> AgentEvent :
        return cls(
            type=AgentEventType.AGENT_FINISHED,
            data={"message":repsonse, "usage": usage.__dict__ if usage else None},
            
            
        )
        
    @classmethod
    def agent_error(cls,error:str,details: dict[str, Any] | None = None )-> AgentEvent :
        return cls(
            type=AgentEventType.AGENT_ERROR,
            data={"error":error, "details": details or {}},

        )
        
    @classmethod
    def text_delta(cls,content :str | None = None)-> AgentEvent :
        return cls(
            type=AgentEventType.TEXT_DELTA,
            data={"content":content},

        )
    @classmethod
    def text_complete(cls,content :str | None = None)-> AgentEvent :
        return cls(
            type=AgentEventType.TEXT_COMPLETE,
            data={"content":content},

        ) 