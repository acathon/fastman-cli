"""
Base classes for CLI commands.
"""
import re
import threading
from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Tuple
from pathlib import Path
from ..utils import PackageManager, NameValidator

class CommandContext:
    """Context passed to commands"""
    _cached_manager = None
    _cached_prefix = None
    _cached_cwd = None
    _lock = threading.Lock()

    @staticmethod
    def _cache_is_stale(project_root):
        """Check if cached values are stale. Safe against None and comparison errors."""
        try:
            return CommandContext._cached_cwd is None or CommandContext._cached_cwd != project_root
        except (TypeError, AttributeError):
            return True

    def __init__(self):
        self.project_root = Path.cwd()
        # Double-check locking: skip lock if cache is fresh
        if CommandContext._cache_is_stale(self.project_root):
            with CommandContext._lock:
                if CommandContext._cache_is_stale(self.project_root):
                    CommandContext._cached_manager, CommandContext._cached_prefix = PackageManager.detect()
                    CommandContext._cached_cwd = self.project_root
        with CommandContext._lock:
            self.package_manager = CommandContext._cached_manager
            self.run_prefix = CommandContext._cached_prefix


class Command(ABC):
    """Base command class"""
    signature: str = ""
    description: str = ""
    help: str = ""  # Optional extended help text with examples

    def __init__(self, args: List[str], context: Optional[CommandContext] = None):
        self.args = args
        self.context = context or CommandContext()

        # Auto-intercept --help / -h
        if "--help" in args or "-h" in args:
            self.show_help()
            self._help_shown = True
        else:
            self._help_shown = False

    @abstractmethod
    def handle(self):
        """Execute the command"""
        pass

    def argument(self, index: int, default: Optional[str] = None) -> Optional[str]:
        """Get positional argument"""
        try:
            return self.args[index]
        except IndexError:
            return default

    def option(self, name: str, default: Optional[str] = None) -> Optional[str]:
        """Get named option (--name=value or --name value)"""
        prefix = f"--{name}="
        flag = f"--{name}"
        
        for i, arg in enumerate(self.args):
            # Handle --name=value format
            if arg.startswith(prefix):
                return arg[len(prefix):]
            # Handle --name value format
            if arg == flag and i + 1 < len(self.args):
                next_arg = self.args[i + 1]
                # Make sure next arg is not another flag
                if not next_arg.startswith("-"):
                    return next_arg
        return default

    def flag(self, name: str) -> bool:
        """Check if flag is present (--flag)"""
        return f"--{name}" in self.args

    def validate_name(self, name: Optional[str], error_msg: str = "Name is required") -> str:
        """Validate and return name"""
        if not name:
            raise ValueError(error_msg)
        return NameValidator.validate_identifier(name)

    # ── Help System ──────────────────────────────────────────────────

    @classmethod
    def parse_signature(cls) -> Tuple[str, List[dict], List[dict], List[dict]]:
        """
        Parse the signature DSL into structured components.
        
        Returns:
            (command_name, arguments, options, flags)
            
        Signature DSL:
            {name}          → positional argument (required)
            {name?}         → positional argument (optional)
            {--option=}     → option (no default)
            {--option=val}  → option with default
            {--flag}        → boolean flag
        """
        sig = cls.signature
        if not sig:
            return cls.__name__, [], [], []

        parts = sig.split()
        command_name = parts[0] if parts else cls.__name__

        arguments = []
        options = []
        flags = []

        for part in parts[1:]:
            # Strip curly braces
            match = re.match(r'\{(.+)\}', part)
            if not match:
                continue

            inner = match.group(1)

            if inner.startswith("--"):
                # Option or flag
                inner = inner[2:]  # Remove --
                if "=" in inner:
                    # Option with optional default
                    name, default = inner.split("=", 1)
                    options.append({
                        "name": name,
                        "default": default if default else None,
                    })
                else:
                    # Boolean flag
                    flags.append({"name": inner})
            else:
                # Positional argument
                optional = inner.endswith("?")
                arg_name = inner.rstrip("?")
                arguments.append({
                    "name": arg_name,
                    "optional": optional,
                })

        return command_name, arguments, options, flags

    def show_help(self):
        """Display formatted help for this command."""
        from ..console import Output, Style

        command_name, arguments, options, flags = self.parse_signature()

        # ── Header ──
        Output.new_line()
        print(f"{Style.BOLD}{Style.CYAN}Usage:{Style.RESET}")

        # Build usage line
        usage_parts = [f"  fastman {command_name}"]
        for arg in arguments:
            if arg["optional"]:
                usage_parts.append(f"[{arg['name']}]")
            else:
                usage_parts.append(f"<{arg['name']}>")
        for opt in options:
            if opt["default"] is not None:
                usage_parts.append(f"[--{opt['name']}={opt['default']}]")
            else:
                usage_parts.append(f"[--{opt['name']}=<value>]")
        for flg in flags:
            usage_parts.append(f"[--{flg['name']}]")
        # Always show --help
        usage_parts.append("[--help]")

        print(" ".join(usage_parts))
        Output.new_line()

        # ── Description ──
        print(f"{Style.BOLD}{Style.CYAN}Description:{Style.RESET}")
        print(f"  {self.description}")
        Output.new_line()

        # ── Arguments ──
        if arguments:
            print(f"{Style.BOLD}{Style.CYAN}Arguments:{Style.RESET}")
            for arg in arguments:
                req = "optional" if arg["optional"] else "required"
                print(f"  {Style.GREEN}{arg['name']:20s}{Style.RESET} {req}")
            Output.new_line()

        # ── Options ──
        if options:
            print(f"{Style.BOLD}{Style.CYAN}Options:{Style.RESET}")
            for opt in options:
                default_str = f" (default: {opt['default']})" if opt["default"] else ""
                print(f"  {Style.GREEN}--{opt['name']:18s}{Style.RESET}{default_str}")
            Output.new_line()

        # ── Flags ──
        all_flags = list(flags) + [{"name": "help"}]
        print(f"{Style.BOLD}{Style.CYAN}Flags:{Style.RESET}")
        for flg in all_flags:
            if flg["name"] == "help":
                print(f"  {Style.GREEN}--help, -h           {Style.RESET}Show this help message")
            else:
                print(f"  {Style.GREEN}--{flg['name']:18s}{Style.RESET}")
        Output.new_line()

        # ── Extended help (examples) ──
        if self.help:
            print(f"{Style.BOLD}{Style.CYAN}Examples:{Style.RESET}")
            for line in self.help.strip().split("\n"):
                print(f"  {line}")
            Output.new_line()


# Command Registry
COMMAND_REGISTRY: Dict[str, type] = {}

def register(cls: type) -> type:
    """Decorator to register commands"""
    cmd_name = cls.signature.split()[0] if cls.signature else cls.__name__
    COMMAND_REGISTRY[cmd_name] = cls
    return cls
