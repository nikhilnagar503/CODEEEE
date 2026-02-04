from Ui.tui import TUI, get_console
from agent.agent import Agent
from agent.events import AgentEvent , AgentEventType
from client.llm_client import llm_client
import asyncio
import click
import sys

console = get_console()

class CLI:
    def __init__(self):
        self.agent  : Agent  | None = None
        self.tui =  TUI(console=console)
        
    async def run_single(self, message:str)-> str | None :
         async with Agent() as agent:
            self.agent = agent
            return await self._process_message(message)

    async def _process_message(self, message:str) -> str | None  :
        if not self.agent :
            return None
        
        assitant_streaming = False 
        final_response : str | None = None
         
        async for event in self.agent.run(message):
            if  event.type == AgentEventType.TEXT_DELTA :
                content = event.data.get("content","")
                if not assitant_streaming:
                    self.tui.begin_assistant()
                    assitant_streaming = True 
                self.tui.stream_response_delta(content)
            elif event.type == AgentEventType.TEXT_COMPLETE :
                final_response = event.data.get("content","")
                if assitant_streaming :
                    self.tui.end_assistant()
                    assitant_streaming = False
                    console.print("\n[success]Agent finished processing the message.[/success]")
            elif event.type == AgentEventType.AGENT_ERROR:
                  error = event.data.get("error","Unknown error occurred.")
                  if assitant_streaming :
                      console.print(f"\n[error]{error}[/error]")
                      
        return final_response



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
        result  = asyncio.run(cli.run_single(prompt))
        
        if result is None :
            sys.exit(1)
    
    
    

if __name__ == "__main__":
       main()