from pydantic import BaseModel , Field


class ReadFileParams(BaseModel):
    
    path : str : Field(..., description="the path of the file to read")