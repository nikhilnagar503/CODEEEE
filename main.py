from client.llm_client import llm_client
import asyncio

async def main():
    client = llm_client()
    
    messages = [
        {"role": "user", "content": "Hello, how are you?"}
    ]
    
    async for event in client.chat_completion(messages, stream=True):
        print(event)
    await client.close()

if __name__ == "__main__":
    asyncio.run(main())