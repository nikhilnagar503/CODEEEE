from rich.console import Console
from rich.theme import Theme


AGENT_THEME = Theme(
    {
        # General
        "info": "cyan",
        "warning": "yellow",
        "error": "bright_red bold",
        "success": "green",
        "dim": "dim",
        "muted": "grey50",
        "border": "grey35",
        "highlight": "bold cyan",
        # Roles
        "user": "bright_blue bold",
        "assistant": "bright_white",
        # Tools
        "tool": "bright_magenta bold",
        "tool.read": "cyan",
        "tool.write": "yellow",
        "tool.shell": "magenta",
        "tool.network": "bright_blue",
        "tool.memory": "green",
        "tool.mcp": "bright_cyan",
        # Code / blocks
        "code": "white",
    }
)

_console : Console | None = None


def get_console()-> Console :
    global _console
    if _console is None:
       _console = Console(theme=AGENT_THEME , highlight=False)
       
       
    return _console 



class TUI:
    def __init__(self , console : Console | None = None):
        self.console = console or get_console()
        
    def stream_response_delta(self, content : str):
        self.console.print(content , end="" ,markup=False)
    
    
    def stream_assistan_delta(self, content : str):
        self.console.print(f"[assistant]{content}[/assistant]", end="" )
    def print_info(self, message: str):
        self.console.print(f"[info]{message}[/info]")

    def print_warning(self, message: str):
        self.console.print(f"[warning]{message}[/warning]")

    def print_error(self, message: str):
        self.console.print(f"[error]{message}[/error]")

    def print_success(self, message: str):
        self.console.print(f"[success]{message}[/success]")