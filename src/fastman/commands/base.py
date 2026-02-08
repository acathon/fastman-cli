"""
Base classes for CLI commands.
"""
from abc import ABC, abstractmethod
from typing import List, Optional, Dict
from pathlib import Path
from ..utils import PackageManager, NameValidator

class CommandContext:
    """Context passed to commands"""
    # Class-level cache for package manager detection
    _cached_manager = None
    _cached_prefix = None
    _cached_cwd = None
    
    def __init__(self):
        self.project_root = Path.cwd()
        # Use cached values if we're in the same directory
        if CommandContext._cached_cwd != self.project_root:
            CommandContext._cached_manager, CommandContext._cached_prefix = PackageManager.detect()
            CommandContext._cached_cwd = self.project_root
        self.package_manager = CommandContext._cached_manager
        self.run_prefix = CommandContext._cached_prefix


class Command(ABC):
    """Base command class"""
    signature: str = ""
    description: str = ""

    def __init__(self, args: List[str], context: Optional[CommandContext] = None):
        self.args = args
        self.context = context or CommandContext()

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


# Command Registry
COMMAND_REGISTRY: Dict[str, type] = {}

def register(cls: type) -> type:
    """Decorator to register commands"""
    cmd_name = cls.signature.split()[0] if cls.signature else cls.__name__
    COMMAND_REGISTRY[cmd_name] = cls
    return cls
