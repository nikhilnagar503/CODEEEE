from pydantic import BaseModel , Field
from Tool.base import Tool, ToolInvocation, ToolKind, ToolResult
from utils.paths import resolve_path , is_binary_file


class ReadFileParams(BaseModel):
    
    path : str = Field(..., description="the path of the file to read")
    
    offset : int = Field(1,ge= 1, description="the offset to start reading from line number, default is 1")
    
    
    limit : int | None  = Field(ge=1, description="maximum number of lines to read, default is None which means read the whole file")
    
    
    
    
    
class ReadFileTool(Tool):
    name = "read_file"
    description = ("Read the content of a  text file . Return the file content with  line numbers " ,
                   "For the large file , use the offset and limit parameters to read the specific portion of the file",
                   " cannot read the binary file or the file larger than 10 MB"
                   
                )
    
    kind = ToolKind.READ
    
    schema = ReadFileParams
    
    MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB
    async def execute(self, invocation: ToolInvocation) -> ToolResult:
        params = ReadFileParams(**invocation.params)
        path = resolve_path(invocation.cwd, params.path)
        
        
        if not path.exists():
            return ToolResult.error_result(f"File not found: {path}")
        if not path.is_file():
            return ToolResult.error_result(f"Path is not a file: {path}")
        
        file_size = path.stat().st_size
        
        if file_size > self.MAX_FILE_SIZE:
            return ToolResult.error_result(f"File is too large to read (size: {file_size} bytes)")
        
        if is_binary_file(path):
            return ToolResult.error_result("Cannot read binary files")