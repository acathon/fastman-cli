"""
Base classes for CLI commands.
"""
from abc import ABC, abstractmethod
from typing import List, Optional, Dict
from pathlib import Path
from ..utils import PackageManager, NameValidator

class CommandContext:
    """Context passed to commands"""
    def __init__(self):
        self.project_root = Path.cwd()
        self.package_manager, self.run_prefix = PackageManager.detect()


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
        """Get named option (--name=value)"""
        prefix = f"--{name}="
        for arg in self.args:
            if arg.startswith(prefix):
                return arg[len(prefix):]
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
