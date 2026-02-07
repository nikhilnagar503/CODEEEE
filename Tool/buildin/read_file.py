from pydantic import BaseModel , Field
from Tool.base import Tool, ToolKind


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
                   
                   
                   
    