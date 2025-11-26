"""
Fastman - The Complete FastAPI CLI Framework

A Fastman CLI for FastAPI that makes building APIs a breeze.
"""

from .cli import main, __version__, CLI, Command, COMMAND_REGISTRY

__all__ = [
    "main",
    "__version__",
    "CLI",
    "Command",
    "COMMAND_REGISTRY",
]

__author__ = "Fastman Contributors"
__license__ = "MIT"