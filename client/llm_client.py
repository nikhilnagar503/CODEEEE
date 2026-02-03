from openai import AsyncOpenAI
from typing import Any, AsyncGenerator
from dotenv import load_dotenv
import os


from client.response import TextDelta, TokenUsage , StreamEvent , EventType

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
                              stream : bool = True
            
                              )-> AsyncGenerator[StreamEvent , None]:
        client = self.get_client()
        kwargs = {
            "model": os.getenv("MODEL"),
            "messages": messages,
            "stream": stream,
            "temperature": 0.7,
            "max_tokens": 1000
        }
        
        # Debug: Check if env variables are loaded
        print(f"MODEL: {os.getenv('MODEL')}")
        print(f"API_KEY: {os.getenv('OPENAI_API_KEY')[:10] if os.getenv('OPENAI_API_KEY') else 'NOT SET'}")
        print(f"BASE_URL: {os.getenv('BASE_URL')}")
        
        if stream:
            async for event in self._stream_response(client, kwargs):
                yield event
        else:
            event = await self._non_stream_response(client, kwargs)
            yield event
        
        return
    
    
    async def _stream_response(self, client:AsyncOpenAI, kwargs:dict[str, Any]) -> AsyncGenerator[StreamEvent , None]:
        response = await client.chat.completions.create(**kwargs)
        
        async for chunk in response:
            yield chunk
        
        
    async def _non_stream_response( self, client: AsyncOpenAI,kwargs : dict[str, Any])   -> StreamEvent :
        
        
        response = await client.chat.completions.create(**kwargs)
        choice = response.choices[0]    
        message = choice.message
        text_delta = None
        
        if message.content:
            text_delta = TextDelta(content=message.content)
        
        usage = None
        if response.usage:
            usage = TokenUsage(
                prompt_tokens=response.usage.prompt_tokens,
                completion_tokens=response.usage.completion_tokens,
                total_tokens=response.usage.total_tokens,
                cached_tokens=response.usage.prompt_tokens_details.cached_tokens,  # Assuming cached tokens is not provided by OpenAI
            )
        return StreamEvent(
            event_type = EventType.MESSAGE_COMPLETE ,
            text_delta = text_delta,
            finish_reason= choice.finish_reason,
            usage = usage,
            error = "",
            )
        
       