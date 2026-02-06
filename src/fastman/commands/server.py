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

    def handle(self):
        host = self.option("host", "127.0.0.1")
        port = self.option("port", "8000")

        # Reload is enabled by default unless --no-reload is specified
        reload_flag = self.flag("reload")
        no_reload_flag = self.flag("no-reload")

        reload = True
        if no_reload_flag:
            reload = False
        elif reload_flag:
            reload = True

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
