"""
Server commands.
"""
import subprocess
from .base import Command, register
from ..console import Output
from ..utils import PackageManager

@register
class ServeCommand(Command):
    signature = "serve {--host=127.0.0.1} {--port=8000} {--reload}"
    description = "Start development server"

    def handle(self):
        host = self.option("host", "127.0.0.1")
        port = self.option("port", "8000")
        reload = self.flag("reload") or True  # Default to reload in dev

        cmd = PackageManager.get_run_prefix() + [
            "uvicorn",
            "app.main:app",
            "--host", host,
            "--port", port
        ]

        if reload:
            cmd.append("--reload")

        Output.info(f"Starting server at http://{host}:{port}")
        Output.info("Press CTRL+C to stop")

        try:
            subprocess.run(cmd)
        except KeyboardInterrupt:
            Output.info("\nShutting down server...")
