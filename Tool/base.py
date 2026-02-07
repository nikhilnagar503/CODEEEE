from __future__ import annotations
import abc
from pathlib import Path
from dataclasses import dataclass, field
from typing import Any

from enum import Enum
from pydantic.json_schema import model_json_schema 
from pydantic import BaseModel

class ToolKind(str, Enum):
    READ : str = "read"
    WRITE : str = "write"
    SHELL : str = "shell"  # CAMMAND LINE OPERATION
    NETWORK : str = "network"
    MEMORY : str = "memory"
    MCP  =  "mcp"

@dataclass
class  ToolResult:
    success : bool
    output : str | None = None
    error : str | None = None
    metadata : dict[str,Any]  = field(default_factory=dict)

    @classmethod
    def error_result (cls , error_msg : str , output: str | None = ""):
        return cls(
            success = False,
            output = output,
            error = error_msg,
        
             
        )
        
    @classmethod
    def success_result(cls, output: str | None = "", metadata: dict[str,Any] | None = None):
        return cls(
            success=True,
            output=output,
            error=None,
            metadata=metadata or {}
        )
        
        
        
        
        
@dataclass 
class ToolInvocation:
    params : dict[str,Any]
    cwd : Path   
    
@dataclass
class ToolConfirmation:
    tool_name : str 
    params : dict[str,Any]
    description : str |None = None 
    
    
    
class Tool(abc.ABC):
    name : str = "base_tool"
    description : str = "Base tool "
    kind : ToolKind = ToolKind.READ
    
    def __init__(self, name: str, description: str):
        pass 
    
    @property
    def schema(self)->dict[str,Any] | type['BaseModel']:
        raise NotImplementedError("Tool must be define with schema property")
    
    
    @abc.abstractmethod
    async def run(self, invocation)-> ToolResult:
        pass 
    
    def validate_params(self,params : dict[str,Any])-> list[str]:
        schema = self.schema
        if isinstance(schema,type) and issubclass(schema , BaseModel):
            try :
                
              schema(**params)
            except Exception as e:
                error = []
                for err in e.errors():
                  field =".".join(str(x) for x in error.get("loc",[]))
                  msg = error.get("msg","validation error")
                  error.append(f"{field} : {msg}")
                return error
            except Exception as e:
                return [str(e)]
        return []
    
    
    def  is_mutating(self,parameters:dict[str,Any])-> bool:   # just checking that tool we are calling is the mutating or non mutating 
        return self.kind in {ToolKind.WRITE,
                             ToolKind.SHELL,
                             ToolKind.NETWORK,
                             ToolKind.MCP,
                             ToolKind.MEMORY
                            }
    async def get_confirmation(self,invocation:ToolInvocation) -> ToolInvocation:
        if not self.is_mutating(invocation.params):
            return None 
                                
        return ToolConfirmation(
            tool_name = self.name,
            params = invocation.params,
            description = self.description
        )
    
    def to_openai_schema(self,) -> dict[str,Any]:
        schema = self.schema 
        if isinstance(schema,type) and issubclass(schema , BaseModel):  # if it is pydantic schema 
            json_schema = model_json_schema(schema , mode="serialization")
            
            
            
            return {
                'name': self.name,
                'description': self.description,
                'parameters': {
                    'type': 'object',
                    'properties': json_schema.get("properties", {}),
                    'required': json_schema.get("required", []),
                }
            }    # this is the way how open is expecting the tool schema to be
            
        if isinstance(schema, dict):  # if it is dict schema
            result =  {
                'name': self.name,'description': self.description}
            
            if 'parameters' in schema:
                result['parameters'] = schema['parameters']
            else: result['parameters'] = schema 
            
            
            return result 
        raise ValueError("Invalid schema type. Schema must be either a Pydantic model or a dictionary.")    
    
                   