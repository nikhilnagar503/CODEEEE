from openai import AsyncOpenAI
from typing import Any, AsyncGenerator
from dotenv import load_dotenv
import os
from openai import RateLimitError, APIConnectionError , APIError
import asyncio


from client.response import TextDelta, TokenUsage , StreamEventType , StreamEvent

class llm_client:
    def __init__(self) -> None:
        self._client: AsyncOpenAI | None = None
        self._max_retries : int  = 3
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
        
        for attempt in range(self._max_retries+1):
            try : 
                client = self.get_client()
                kwargs = {
                    "model": os.getenv("MODEL"),
                    "messages": messages,
                    "stream": stream,
                    "temperature": 0.7,
                    "max_tokens": 1000
                }
                
                if stream:
                    async for event in self._stream_response(client, kwargs):
                        yield event
                else:
                    event = await self._non_stream_response(client, kwargs)
                    yield event
                return
            
            
            except RateLimitError as e :
                if attempt < self._max_retries:
                    await asyncio.sleep(2 ** attempt)  # Exponential backoff
                    continue
                else:
                    yield StreamEvent(
                        event_type=StreamEventType.ERROR,
                        error = f"Rate limit exceeded: {str(e)} "
                    )
                return 
                    
            except APIConnectionError as e:
                if attempt < self._max_retries:
                    await asyncio.sleep(2 ** attempt)  # Exponential backoff
                    continue
                else:
                    yield StreamEvent(
                        event_type=StreamEventType.ERROR,
                        error = f"Connection error: {str(e)} "
                    )
                return 
            except APIError as e:
                yield StreamEvent(
                    event_type=StreamEventType.ERROR,
                    error=f"API error: {e}",
                )
                return
    
    
    async def _stream_response(self, client:AsyncOpenAI, kwargs:dict[str, Any]) -> AsyncGenerator[StreamEvent , None]:
        response = await client.chat.completions.create(**kwargs)
        finish_reason : str | None = None
        usage : TokenUsage | None = None
        
        async for chunk in response:
            if hasattr(chunk,'usage') and chunk.usage:
                usage = TokenUsage(
                    prompt_tokens=chunk.usage.prompt_tokens,
                    completion_tokens=chunk.usage.completion_tokens,
                    total_tokens=chunk.usage.total_tokens,
                    cached_tokens=chunk.usage.prompt_tokens_details.cached_tokens,  # Assuming cached tokens is not provided by OpenAI
                )
                
            if not chunk.choices:
                continue
            
            choice = chunk.choices[0]
            delta = choice.delta
            
            if delta.content:
                text_delta = TextDelta(content=delta.content)
                stream_event = StreamEvent(
                    event_type=StreamEventType.TEXT_DELTA,
                    text_delta=text_delta,
        
                )
                yield stream_event
                
            
        yield StreamEvent(  
            event_type=StreamEventType.MESSAGE_COMPLETE,
            finish_reason=choice.finish_reason,
            usage=usage,
        )
        
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
            event_type = StreamEventType.MESSAGE_COMPLETE ,
            text_delta = text_delta,
            finish_reason= choice.finish_reason,
            usage = usage,
            error = "",
            )
        
       