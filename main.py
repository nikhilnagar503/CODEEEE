from Ui.tui import TUI, get_console
from agent.agent import Agent
from agent.events import AgentEvent , AgentEventType
from client.llm_client import llm_client
import asyncio
import click

console = get_console()

class CLI:
    def __init__(self):
        self.agent  : Agent  | None = None
        self.tui =  TUI(console=console)
        
    async def run_single(self, message:str):
         async with Agent() as agent:
            self.agent = agent
            await self._process_message(message)

    async def _process_message(self, message:str) -> str | None  :
        if not self.agent :
            return None
        
        async for event in self.agent.run(message):
            if  event.type == AgentEventType.TEXT_DELTA :
                content = event.data.get("content","")
                self.tui.stream_response_delta(content)
                


async def run (message:dict[str,any]):
    client = llm_client()
    async for event in client.chat_completion([message],stream=True):
        print(event)
    await client.close()




@click.command()
@click.argument("prompt",required=False)
def main(
    prompt: str | None 
):
    if prompt is None:
        print("Please provide a prompt")
        return
    
    
    
    cli = CLI()
    
    messages = [
        {"role": "user", "content": prompt}
    ]
    
    if prompt:
        asyncio.run(cli.run_single(prompt))
    
    
    

if __name__ == "__main__":
       main()