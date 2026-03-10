"""
Server commands.
"""
import subprocess
from .base import Command, register
from ..console import Output
from ..utils import PackageManager

@register
class ServeCommand(Command):
    signature = "serve {--host=127.0.0.1} {--port=8000} {--reload} {--no-reload}"
    description = "Start development server"
    help = """
Examples:
  fastman serve
  fastman serve --port=8080
  fastman serve --host=0.0.0.0 --no-reload
"""

    def handle(self):
        host = self.option("host", "127.0.0.1")
        port = self.option("port", "8000")

        if self.flag("no-reload"):
            reload = False
        elif self.flag("reload"):
            reload = True
        else:
            reload = True

        cmd = PackageManager.get_run_prefix() + [
            "python",
            "-m",
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
