"""
Main entry point for the CLI.
"""
import sys
import logging
from pathlib import Path
import importlib
from typing import List

from .commands.base import CommandContext, COMMAND_REGISTRY
from .console import Output, logger
# Import commands to ensure registration
from .commands import (
    project,
    server,
    scaffold,
    database,
    auth,
    misc
)

class CLI:
    """Main CLI application"""

    def __init__(self):
        self.context = CommandContext()
        self.load_custom_commands()

    def load_custom_commands(self):
        """Load custom commands from app/console/commands"""
        commands_path = Path("app/console/commands")

        if not commands_path.exists():
            return

        sys.path.insert(0, str(Path.cwd()))

        for file_path in commands_path.glob("*.py"):
            if file_path.name.startswith("_"):
                continue

            module_name = file_path.stem
            try:
                importlib.import_module(f"app.console.commands.{module_name}")
                logger.debug(f"Loaded custom command: {module_name}")
            except (ImportError, AttributeError) as e:
                logger.error(f"Failed to load custom command {module_name}: {e}")

    def run(self, args: List[str]):
        """Run CLI with arguments"""
        if not args or args[0] in ["-h", "--help"]:
            misc.ListCommand([], self.context).handle()
            return

        command_name = args[0]
        command_args = args[1:]

        # Handle special flags
        if command_name == "--version" or command_name == "-v":
            misc.VersionCommand([], self.context).handle()
            return

        # Find and execute command
        if command_name in COMMAND_REGISTRY:
            command_class = COMMAND_REGISTRY[command_name]

            try:
                command = command_class(command_args, self.context)
                command.handle()
            except ValueError as e:
                Output.error(str(e))
                sys.exit(1)
            except KeyboardInterrupt:
                Output.info("\nOperation cancelled")
                sys.exit(130)
            except Exception as e:
                Output.error(f"An unexpected error occurred: {e}")
                logger.exception(e)
                sys.exit(1)
        else:
            Output.error(f"Unknown command: {command_name}")
            Output.info("Run 'fastman list' to see available commands")
            sys.exit(1)


def main():
    """Main entry point"""
    cli = CLI()
    cli.run(sys.argv[1:])

if __name__ == "__main__":
    main()
