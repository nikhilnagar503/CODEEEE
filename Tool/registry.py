
from pathlib import Path
from typing import Any
# from config.config import Config
# from hooks.hook_system import HookSystem
# from safety.approval import ApprovalContext, ApprovalDecision, ApprovalManager
from Tool.base import Tool, ToolInvocation, ToolResult
import logging
from Tool.builtin import ReadFileTool, get_all_builtin_tools
# from tools.subagents import SubagentTool, get_default_subagent_definitions

logger = logging.getLogger(__name__)
class ToolRegistry:
    def __init__(self):
        self._tools : dict[str,Tool] = {}
        
    def register(self, tool: Tool)-> None :
        if tool.name in self._tools:
            logger.warning(f"Tool with name {tool.name} is already registered. It will be overwritten.")
        self._tools[tool.name] = tool
        logger.info(f"Registered tool: {tool.name}")
        
    def unregister(self, name: str) -> bool:
        if name in self._tools:
            del self._tools[name]
            return True

        return False
    
    def get(self, name: str) -> Tool | None:
        if name in self._tools:
            return self._tools[name]

        return None
    
    
    def get_tools(self) -> list[Tool]:
        tools: list[Tool] = []

        for tool in self._tools.values():
            tools.append(tool)

        return tools
    
    def get_schemas(self) -> list[dict[str, Any]]:
        return [tool.to_openai_schema() for tool in self.get_tools()]
    
    
    
    async def invoke(
        self,
        name: str,
        params: dict[str, Any],
        cwd: Path,
    ) -> ToolResult:
        
        tool = self.get(name)
        if tool is None:
            return ToolResult.error_result(
                f"Unknown tool: {name}",
                metadata={"tool_name": name},
            )
        validation_errors = tool.validate_params(params)
        if validation_errors:
            result = ToolResult.error_result(
                f"Invalid parameters: {'; '.join(validation_errors)}",
                metadata={
                    "tool_name": name,
                    "validation_errors": validation_errors,
                },
            )

            
            return result
    
        invocation = ToolInvocation(params=params, cwd=cwd)
        
        try:
            result = await tool.execute(invocation)
        except Exception as e:
            logger.exception(f"Tool {name} raised unexpected error")
            result = ToolResult.error_result(
                f"Internal error: {str(e)}",
                metadata={
                    "tool_name": name,
                },
            )
        return result



def create_default_registry() -> ToolRegistry:
    registry = ToolRegistry()
    
    BUILTIN_TOOLS = get_all_builtin_tools()
    for tool_cls in BUILTIN_TOOLS:
        registry.register(tool_cls())
    return registry

        
    