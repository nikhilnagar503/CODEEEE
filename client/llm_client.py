from openai import AsyncOpenAI
from typing import Any
from dotenv import load_dotenv
import os

class llm_client:
    def __init__(self) -> None:
        self._client: AsyncOpenAI | None = None
        load_dotenv()  # Load environment variables from .env file
    
    def get_client(self) -> AsyncOpenAI:
        if self._client is None:
            self._client = AsyncOpenAI(
                api_key=os.getenv("OPENAI_API_KEY"),  # Reads from .env file
                base_url=os.getenv("BASE_URL")  # Reads from .env file
            )
        return self._client
    
    async def close(self) -> None:  # Closes the API connection properly
        if self._client:
            await self._client.close()
            self._client = None
            
    async def chat_completion(self,
                              messages : list[dict[str, Any]],
                              stream : bool = False
            
                              ):
        client = self.get_client()
        kwargs = {
            "model": os.getenv("MODEL"),
            "messages": messages,
            "stream": stream
        }
        
        # Debug: Check if env variables are loaded
        print(f"MODEL: {os.getenv('MODEL')}")
        print(f"API_KEY: {os.getenv('OPENAI_API_KEY')[:10] if os.getenv('OPENAI_API_KEY') else 'NOT SET'}")
        print(f"BASE_URL: {os.getenv('BASE_URL')}")
        
        if stream:
            await self._stream_response()
        else :
            await self._non_stream_response(client, kwargs)
    
    
    async def _stream_response(self):
        pass
    async def _non_stream_response(
        self, 
        client: AsyncOpenAI,
        kwargs : dict[str, Any]):
        
        response = await client.chat.completions.create(**kwargs)
        print(response.choices[0].message.content)
                
        
        