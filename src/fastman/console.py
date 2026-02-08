"""
Professional console output and styling utilities for Fastman.
Designed to be better than Laravel CLI with modern UI patterns.
"""
import sys
import time
import logging
import shutil
from enum import Enum
from contextlib import contextmanager
from typing import Optional, List, Tuple, Iterator

# Try to import optional dependencies
try:
    import pyfiglet
    HAS_PYFIGLET = True
except ImportError:
    HAS_PYFIGLET = False

try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.confirm import Confirm
    from rich.table import Table
    from rich.columns import Columns
    from rich.text import Text
    from rich.rule import Rule
    from rich.syntax import Syntax
    from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
    from rich.align import Align
    from rich import box
    from rich.theme import Theme
    HAS_RICH = True
    
    # Custom theme for Fastman
    fastman_theme = Theme({
        "info": "cyan",
        "warning": "yellow",
        "danger": "red",
        "success": "green",
        "brand": "bright_cyan",
        "muted": "dim",
        "highlight": "bright_yellow",
    })
    console = Console(theme=fastman_theme)
except ImportError:
    HAS_RICH = False
    console = None

# Logging setup
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('fastman')

# Get terminal width
TERMINAL_WIDTH = shutil.get_terminal_size().columns or 80


class Style:
    """ANSI color codes for terminal output (fallback)"""
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    MAGENTA = '\033[95m'
    WHITE = '\033[97m'
    BRIGHT_CYAN = '\033[96;1m'
    BRIGHT_GREEN = '\033[92;1m'
    BRIGHT_YELLOW = '\033[93;1m'
    BRIGHT_RED = '\033[91;1m'
    RESET = '\033[0m'
    BOLD = '\033[1m'
    DIM = '\033[2m'
    UNDERLINE = '\033[4m'


class Icons:
    """ASCII icons for different message types (Laravel-style)"""
    SUCCESS = ">"
    ERROR = "x"
    WARNING = "!"
    INFO = ">"
    ARROW = ">"
    BULLET = "*"
    STAR = "*"
    ROCKET = ">>"
    SPARKLES = "*"
    FIRE = "*"
    GEAR = "*"
    DATABASE = "*"
    SERVER = "*"
    LOCK = "*"
    KEY = "*"
    PACKAGE = "*"
    FOLDER = "*"
    FILE = "*"
    CHECK = ">"
    CROSS = "x"


class OutputLevel(Enum):
    """Output verbosity levels"""
    SUCCESS = "success"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    DEBUG = "debug"


class Output:
    """
    Professional CLI output handler with Rich support and fallback.
    Designed to be better than Laravel CLI with modern UI patterns.
    """
    
    @staticmethod
    def echo(msg: str, style: str = "", end: str = "\n"):
        """Basic echo with style"""
        if HAS_RICH and console:
            console.print(msg, end=end)
        else:
            print(f"{style}{msg}{Style.RESET}", end=end)
    
    @staticmethod
    def line():
        """Print a horizontal line"""
        if HAS_RICH:
            console.print(Rule(style="dim"))
        else:
            print("─" * TERMINAL_WIDTH)
    
    @staticmethod
    def new_line(count: int = 1):
        """Print new lines"""
        for _ in range(count):
            print()
    
    @staticmethod
    def success(msg: str, icon: bool = True, prefix: str = ""):
        """
        Success message with professional styling.
        
        Args:
            msg: Message to display
            icon: Whether to show success icon
            prefix: Optional prefix text
        """
        icon_str = f"{Icons.SUCCESS} " if icon else ""
        prefix_str = f"{prefix} " if prefix else ""
        
        if HAS_RICH:
            console.print(f"[success]{icon_str}[/success]{prefix_str}{msg}")
        else:
            try:
                print(f"{Style.BRIGHT_GREEN}{icon_str}{Style.RESET}{prefix_str}{msg}")
            except UnicodeEncodeError:
                print(f"{Style.GREEN}[OK]{Style.RESET} {prefix_str}{msg}")
        logger.info(msg)
    
    @staticmethod
    def info(msg: str, icon: bool = True, dim: bool = False):
        """
        Info message with professional styling.
        
        Args:
            msg: Message to display
            icon: Whether to show info icon
            dim: Whether to dim the output
        """
        icon_str = f"{Icons.INFO} " if icon else ""
        style = "muted" if dim else "info"
        
        if HAS_RICH:
            console.print(f"[{style}]{icon_str}{msg}[/{style}]")
        else:
            try:
                print(f"{Style.BLUE}{icon_str}{Style.RESET}{msg}")
            except UnicodeEncodeError:
                print(f"{Style.BLUE}[INFO]{Style.RESET} {msg}")
        logger.info(msg)
    
    @staticmethod
    def warn(msg: str, icon: bool = True):
        """Warning message with professional styling"""
        icon_str = f"{Icons.WARNING} " if icon else ""
        
        if HAS_RICH:
            console.print(f"[warning]{icon_str}{msg}[/warning]")
        else:
            try:
                print(f"{Style.YELLOW}{icon_str}{Style.RESET}{msg}")
            except UnicodeEncodeError:
                print(f"{Style.YELLOW}[WARN]{Style.RESET} {msg}")
        logger.warning(msg)
    
    @staticmethod
    def error(msg: str, icon: bool = True, exit_code: Optional[int] = None):
        """
        Error message with professional styling.
        
        Args:
            msg: Error message
            icon: Whether to show error icon
            exit_code: Optional exit code to exit with
        """
        icon_str = f"{Icons.ERROR} " if icon else ""
        
        if HAS_RICH:
            console.print(f"[danger]{icon_str}{msg}[/danger]")
        else:
            try:
                print(f"{Style.BRIGHT_RED}{icon_str}{Style.RESET}{msg}")
            except UnicodeEncodeError:
                print(f"{Style.RED}[ERROR]{Style.RESET} {msg}")
        logger.error(msg)
        
        if exit_code is not None:
            sys.exit(exit_code)
    
    @staticmethod
    def comment(msg: str):
        """Comment/secondary text (dimmed)"""
        if HAS_RICH:
            console.print(f"[muted]{msg}[/muted]")
        else:
            print(f"{Style.DIM}{msg}{Style.RESET}")
    
    @staticmethod
    def highlight(msg: str, icon: str = ""):
        """Highlighted important text"""
        icon_str = f"{icon} " if icon else ""
        if HAS_RICH:
            console.print(f"[highlight]{icon_str}{msg}[/highlight]")
        else:
            print(f"{Style.BRIGHT_YELLOW}{icon_str}{msg}{Style.RESET}")
    
    @staticmethod
    def task(title: str, status: str = "running", status_style: str = "yellow"):
        """
        Display a task with status indicator.
        
        Args:
            title: Task title
            status: Status text (running, done, failed)
            status_style: Rich style for status
        """
        if HAS_RICH:
            status_text = f"[{status_style}]{status}[/{status_style}]"
            console.print(f"  {Icons.ARROW} {title} ... {status_text}")
        else:
            print(f"  → {title} ... [{status}]")
    
    @staticmethod
    def section(title: str, description: str = ""):
        """
        Display a section header.
        
        Args:
            title: Section title
            description: Optional description
        """
        if HAS_RICH:
            text = Text()
            text.append(title, style="bold cyan")
            if description:
                text.append(f" - {description}", style="dim")
            console.print(Rule(text, style="cyan"))
        else:
            print()
            print(f"{Style.BOLD}{Style.CYAN}▶ {title}{Style.RESET}")
            if description:
                print(f"  {Style.DIM}{description}{Style.RESET}")
            print()
    
    @staticmethod
    def listing(items: List[Tuple[str, str]], title: str = None, icon: str = Icons.BULLET):
        """
        Display a formatted list of items.
        
        Args:
            items: List of (label, description) tuples
            title: Optional title
            icon: Icon to use for each item
        """
        if title:
            Output.section(title)
        
        if HAS_RICH:
            for label, description in items:
                console.print(f"  {icon} [highlight]{label}[/highlight] - {description}")
        else:
            for label, description in items:
                print(f"  {icon} {Style.BRIGHT_YELLOW}{label}{Style.RESET} - {description}")
    
    @staticmethod
    def file_created(path: str, description: str = ""):
        """Display a file creation message"""
        desc = f" ({description})" if description else ""
        if HAS_RICH:
            console.print(f"  {Icons.FILE} [green]Created[/green] [highlight]{path}[/highlight]{desc}")
        else:
            print(f"  {Icons.FILE} Created {path}{desc}")
    
    @staticmethod
    def directory_created(path: str):
        """Display a directory creation message"""
        if HAS_RICH:
            console.print(f"  {Icons.FOLDER} [green]Created directory[/green] [highlight]{path}[/highlight]")
        else:
            print(f"  {Icons.FOLDER} Created directory {path}")
    
    @staticmethod
    def next_steps(steps: List[Tuple[str, str]]):
        """
        Display next steps in a formatted way.
        
        Args:
            steps: List of (command, description) tuples
        """
        if HAS_RICH:
            console.print(f"\n[bold cyan]{Icons.ROCKET} Next steps:[/bold cyan]")
            for cmd, desc in steps:
                console.print(f"  [highlight]{cmd}[/highlight] - {desc}")
        else:
            print(f"\n{Style.BOLD}{Icons.ROCKET} Next steps:{Style.RESET}")
            for cmd, desc in steps:
                print(f"  {Style.BRIGHT_YELLOW}{cmd}{Style.RESET} - {desc}")
    
    @staticmethod
    def banner(version: str):
        """
        Display a professional application banner (Laravel-style).
        """
        if HAS_PYFIGLET:
            # Try different fonts for a clean look
            fonts = ["slant", "small", "standard"]
            banner_text = None
            
            for font in fonts:
                try:
                    banner_text = pyfiglet.figlet_format("Fastman", font=font)
                    break
                except:
                    continue
            
            if banner_text is None:
                banner_text = pyfiglet.figlet_format("Fastman")
        else:
            # Clean ASCII banner (Laravel-style)
            banner_text = "Fastman"
        
        if HAS_RICH:
            console.print(f"[bold cyan]{banner_text}[/bold cyan]", end="" if HAS_PYFIGLET else "\n")
            console.print(f"[dim]v{version} - The Complete FastAPI CLI Framework[/dim]")
            console.print()
        else:
            if HAS_PYFIGLET:
                print(Style.CYAN + banner_text + Style.RESET, end="")
            else:
                print(f"{Style.BOLD}{Style.CYAN}{banner_text}{Style.RESET}")
            print(f"{Style.DIM}v{version} - The Complete FastAPI CLI Framework{Style.RESET}")
            print()
    
    @staticmethod
    def table(headers: List[str], rows: List[List[str]], title: str = None, 
              show_lines: bool = False, box_style=None):
        """
        Display data in a professional table format.
        
        Args:
            headers: Column headers
            rows: Table rows
            title: Optional table title
            show_lines: Whether to show lines between rows
            box_style: Rich box style (defaults to ROUNDED)
        """
        if HAS_RICH:
            from rich.box import ROUNDED
            table = Table(
                title=title,
                show_header=True,
                header_style="bold bright_cyan",
                show_lines=show_lines,
                box=box_style if box_style else ROUNDED,
                border_style="cyan"
            )
            for header in headers:
                table.add_column(header, overflow="fold")
            for row in rows:
                table.add_row(*row)
            console.print(table)
        else:
            if title:
                print(f"\n{Style.BOLD}{title}{Style.RESET}")
            print("─" * min(80, TERMINAL_WIDTH))
            print(f"{Style.CYAN}{' | '.join(headers)}{Style.RESET}")
            print("─" * min(80, TERMINAL_WIDTH))
            for row in rows:
                print(" | ".join(row))
            print("─" * min(80, TERMINAL_WIDTH))
    
    @staticmethod
    def confirm(message: str, default: bool = False) -> bool:
        """
        Ask for user confirmation with professional styling.
        
        Args:
            message: Question to ask
            default: Default value
            
        Returns:
            Boolean response
        """
        if HAS_RICH:
            return Confirm.ask(message, default=default)
        else:
            default_str = "Y/n" if default else "y/N"
            response = input(f"{message} [{default_str}]: ").strip().lower()
            if not response:
                return default
            return response in ['y', 'yes']
    
    @staticmethod
    def ask(question: str, default: str = "") -> str:
        """
        Ask a question and get text input.
        
        Args:
            question: Question to ask
            default: Default value
            
        Returns:
            User input
        """
        if default:
            prompt = f"{question} [{default}]: "
        else:
            prompt = f"{question}: "
        
        if HAS_RICH:
            console.print(f"[cyan]?[/cyan] {prompt}", end="")
        else:
            print(f"? {prompt}", end="")
        
        response = input().strip()
        return response if response else default
    
    @staticmethod
    def choice(question: str, options: List[str], default: int = 0) -> str:
        """
        Ask user to choose from options.
        
        Args:
            question: Question to ask
            options: List of options
            default: Default option index
            
        Returns:
            Selected option
        """
        if HAS_RICH:
            console.print(f"[cyan]?[/cyan] {question}")
            for i, option in enumerate(options):
                marker = "›" if i == default else " "
                console.print(f"  {marker} [{i+1}] {option}")
            console.print("  Select [1-{}]: ".format(len(options)), end="")
        else:
            print(f"? {question}")
            for i, option in enumerate(options):
                marker = "›" if i == default else " "
                print(f"  {marker} [{i+1}] {option}")
            print("  Select [1-{}]: ".format(len(options)), end="")
        
        try:
            choice = int(input().strip()) - 1
            if 0 <= choice < len(options):
                return options[choice]
        except ValueError:
            pass
        
        return options[default]
    
    @staticmethod
    @contextmanager
    def progress(description: str = "Processing..."):
        """
        Context manager for showing progress.
        
        Usage:
            with Output.progress("Installing packages..."):
                do_something()
        """
        if HAS_RICH:
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console,
            ) as progress:
                task = progress.add_task(description, total=None)
                yield
                progress.update(task, completed=True)
        else:
            print(f"  → {description}...", end=" ", flush=True)
            yield
            print(f"{Style.GREEN}Done{Style.RESET}")
    
    @staticmethod
    def spinner(text: str = "Processing") -> Iterator:
        """
        Create a spinner animation.
        
        Usage:
            for _ in Output.spinner("Loading"):
                do_work()
        """
        if HAS_RICH:
            with console.status(f"[cyan]{text}...[/cyan]", spinner="dots"):
                yield
        else:
            print(f"  → {text}...", end=" ", flush=True)
            yield
            print(f"{Style.GREEN}Done{Style.RESET}")
