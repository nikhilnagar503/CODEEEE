from pydantic import BaseModel , Field
from Tool.base import Tool, ToolInvocation, ToolKind, ToolResult
from utils.paths import resolve_path , is_binary_file
from utils.text import count_tokens , truncate_text


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
    MAX_TOKEN_LIMIT = 25000 # this is the maximum token limit for the model , we can adjust it based on the model we are using
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
        
        
        
        try :
        
            try :
                content = path.read_text(encoding="utf-8", errors="ignore")
            except UnicodeDecodeError:
                content = path.read_text(encoding="latin-1", errors="ignore")
                
                
                
            lines = content.splitlines()
            total_lines = len(lines)
            
            if total_lines == 0:
                return ToolResult.success_result(output="file is empty" , metadata={"total_lines":0})
            
            
            start_idx = max (0 , params.offset - 1)
            
            
            if params.limit is not None:
                end_idx = min(start_idx + params.limit, total_lines)
            else:
                end_idx = total_lines

            selected_lines = lines[start_idx:end_idx]
            formatted_lines = []

            for i, line in enumerate(selected_lines, start=start_idx + 1):
                formatted_lines.append(f"{i:6}|{line}")

            output = "\n".join(formatted_lines)
            token_count = count_tokens(output)

            truncated = False
            if token_count > self.MAX_OUTPUT_TOKENS:
                output = truncate_text(
                    output,
                    self.MAX_OUTPUT_TOKENS,
                    suffix=f"\n... [truncated {total_lines} total lines]",
                )
                truncated = True

            metadata_lines = []
            if start_idx > 0 or end_idx < total_lines:
                metadata_lines.append(
                    f"Showing lines {start_idx+1}-{end_idx} of {total_lines}"
                )

            if metadata_lines:
                header = " | ".join(metadata_lines) + "\n\n"
                output = header + output

            return ToolResult.success_result(
                output=output,
                truncated=truncated,
                metadata={
                    "path": str(path),
                    "total_lines": total_lines,
                    "shown_start": start_idx + 1,
                    "shown_end": end_idx,
                },
            )
        except Exception as e:
              return ToolResult.error_result(f"Failed to read file: {e}")
