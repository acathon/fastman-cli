"""
Console output and styling utilities.
"""
import sys
import logging
from enum import Enum

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
    HAS_RICH = True
    console = Console()
except ImportError:
    HAS_RICH = False
    console = None

# Logging setup
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('fastman')


class Style:
    """ANSI color codes for terminal output"""
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    RESET = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


class OutputLevel(Enum):
    """Output verbosity levels"""
    SUCCESS = "success"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    DEBUG = "debug"


class Output:
    """Handles all CLI output with fallback support"""

    @staticmethod
    def echo(msg: str, style: str = ""):
        """Basic echo with style"""
        if HAS_RICH and console:
            console.print(msg)
        else:
            print(f"{style}{msg}{Style.RESET}")

    @staticmethod
    def success(msg: str):
        """Success message"""
        if HAS_RICH:
            try:
                console.print(f"[green]✔[/green] {msg}")
            except UnicodeEncodeError:
                print(f"{Style.GREEN}[OK] {msg}{Style.RESET}")
        else:
            try:
                print(f"{Style.GREEN}✔ {msg}{Style.RESET}")
            except UnicodeEncodeError:
                print(f"{Style.GREEN}[OK] {msg}{Style.RESET}")
        logger.info(msg)

    @staticmethod
    def info(msg: str):
        """Info message"""
        if HAS_RICH:
            try:
                console.print(f"[blue]ℹ[/blue] {msg}")
            except UnicodeEncodeError:
                print(f"{Style.BLUE}[INFO] {msg}{Style.RESET}")
        else:
            try:
                print(f"{Style.BLUE}ℹ {msg}{Style.RESET}")
            except UnicodeEncodeError:
                print(f"{Style.BLUE}[INFO] {msg}{Style.RESET}")
        logger.info(msg)

    @staticmethod
    def warn(msg: str):
        """Warning message"""
        if HAS_RICH:
            try:
                console.print(f"[yellow]⚠[/yellow] {msg}")
            except UnicodeEncodeError:
                print(f"{Style.YELLOW}[WARN] {msg}{Style.RESET}")
        else:
            try:
                print(f"{Style.YELLOW}⚠ {msg}{Style.RESET}")
            except UnicodeEncodeError:
                print(f"{Style.YELLOW}[WARN] {msg}{Style.RESET}")
        logger.warning(msg)

    @staticmethod
    def error(msg: str):
        """Error message"""
        if HAS_RICH:
            try:
                console.print(f"[red]✖[/red] {msg}")
            except UnicodeEncodeError:
                print(f"{Style.RED}[ERROR] {msg}{Style.RESET}")
        else:
            try:
                print(f"{Style.RED}✖ {msg}{Style.RESET}")
            except UnicodeEncodeError:
                print(f"{Style.RED}[ERROR] {msg}{Style.RESET}")
        logger.error(msg)

    @staticmethod
    def banner(version: str):
        """Display application banner"""
        if HAS_PYFIGLET:
            banner_text = pyfiglet.figlet_format("Fastman", font="slant")
        else:
            banner_text = """
    ███████╗ █████╗ ███████╗████████╗███╗   ███╗ █████╗ ███╗   ██╗
    ██╔════╝██╔══██╗██╔════╝╚══██╔══╝████╗ ████║██╔══██╗████╗  ██║
    █████╗  ███████║███████╗   ██║   ██╔████╔██║███████║██╔██╗ ██║
    ██╔══╝  ██╔══██║╚════██║   ██║   ██║╚██╔╝██║██╔══██║██║╚██╗██║
    ██║     ██║  ██║███████║   ██║   ██║ ╚═╝ ██║██║  ██║██║ ╚████║
    ╚═╝     ╚═╝  ╚═╝╚══════╝   ╚═╝   ╚═╝     ╚═╝╚═╝  ╚═╝╚═╝  ╚═══╝
            """

        if HAS_RICH:
            console.print(Panel(
                banner_text,
                title=f"[bold cyan]Fastman v{version}[/bold cyan]",
                subtitle="The Complete FastAPI CLI",
                border_style="cyan"
            ))
        else:
            Output.echo(banner_text, Style.CYAN)
            Output.echo(f"Version {version} - The Complete FastAPI CLI\n", Style.BOLD)

    @staticmethod
    def table(headers: list, rows: list, title: str = None):
        """Display data in table format"""
        if HAS_RICH:
            table = Table(title=title, show_header=True, header_style="bold cyan")
            for header in headers:
                table.add_column(header)
            for row in rows:
                table.add_row(*row)
            console.print(table)
        else:
            if title:
                Output.echo(f"\n{title}", Style.BOLD)
            Output.echo("-" * 80)
            Output.echo(" | ".join(headers), Style.CYAN)
            Output.echo("-" * 80)
            for row in rows:
                print(" | ".join(row))
            Output.echo("-" * 80)

    @staticmethod
    def confirm(message: str, default: bool = False) -> bool:
        """Ask for user confirmation"""
        if HAS_RICH:
            return Confirm.ask(message, default=default)
        else:
            default_str = "Y/n" if default else "y/N"
            response = input(f"{message} [{default_str}]: ").strip().lower()
            if not response:
                return default
            return response in ['y', 'yes']
