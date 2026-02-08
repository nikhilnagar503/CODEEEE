from email.mime import message
from typing import Any

from prompts.system import get_system_prompt
from dataclasses import dataclass
from utils.text import count_tokens
import os
    
from dotenv import load_dotenv

load_dotenv()
MODEL = os.getenv("MODEL")

@dataclass
class MessageItem:
    role : str
    content : str | None = None
    token_count : int | None = None
    extra : dict[str,Any] | None = None
    
    def To_dict(self) -> dict[str,Any]:
        data = {"role": self.role, "content": self.content or ""}
        if self.extra:
            data.update(self.extra)
        return data
        
    
    
class context_manager:
    def __init__(self)-> None :
        self.system_prompts =  get_system_prompt()  # this is not the role of user neither the role of assistant but it is the context provider that should be the behavior of the agent 
        self._messages : list[MessageItem]= []
        self._model_name = MODEL
    
    def add_user_message(self, content : str) -> None :
        item = MessageItem(role="user", content=content,token_count = count_tokens(content, self._model_name))
        self._messages.append(item)
        
    def add_Assistant_message(self, content: str, extra: dict[str, Any] | None = None) -> None:
        item = MessageItem(
            role="assistant",
            content=content or "",
            token_count=count_tokens(content, self._model_name),
            extra=extra,
        )
        
        self._messages.append(item)

    def add_tool_message(self, tool_call_id: str, content: str) -> None:
        item = MessageItem(
            role="tool",
            content=content or "",
            token_count=count_tokens(content, self._model_name),
            extra={"tool_call_id": tool_call_id},
        )
        self._messages.append(item)
    
    def get_messages(self) -> list[dict[str,str]]:
        messages = []
        if self.system_prompts :
            messages.append({"role": "system", "content": self.system_prompts})
            
        for item in self._messages:
            messages.append(item.To_dict())
        return messages