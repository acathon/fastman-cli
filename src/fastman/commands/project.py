"""
Project setup commands.
"""
import os
import secrets
import subprocess
import shutil
import sys
from pathlib import Path
from .. import __version__
from .base import Command, register
from ..console import Output, Style
from ..utils import NameValidator, PathManager
from ..templates import Template, Templates

@register
class NewCommand(Command):
    signature = "new {name} {--minimal} {--pattern=feature} {--package=uv} {--database=sqlite}"
    description = "Create a new FastAPI project"

    def handle(self):
        name = self.argument(0)
        if not name:
            raise ValueError("Project name is required")
        NameValidator.validate_path_component(name)

        minimal = self.flag("minimal")
        pattern = self.option("pattern", "feature").lower()
        package_manager = self.option("package", "uv").lower()
        database = self.option("database", "sqlite").lower()

        # Validate pattern
        valid_patterns = ["feature", "api", "layer"]
        if pattern not in valid_patterns:
            Output.error(f"Invalid pattern '{pattern}'. Must be one of: {', '.join(valid_patterns)}")
            return

        # Validate package manager
        valid_packages = ["uv", "pipenv", "poetry"]
        if package_manager not in valid_packages:
            Output.error(f"Invalid package manager '{package_manager}'. Must be one of: {', '.join(valid_packages)}")
            return

        # Validate database
        valid_databases = ["sqlite", "postgresql", "mysql", "oracle", "firebase"]
        if database not in valid_databases:
            Output.error(f"Invalid database '{database}'. Must be one of: {', '.join(valid_databases)}")
            return

        project_path = Path(name)

        if project_path.exists():
            Output.error(f"Directory '{name}' already exists")
            return

        Output.info(f"Creating new project: {name}")
        Output.info(f"Pattern: {pattern}")
        Output.info(f"Package Manager: {package_manager}")
        Output.info(f"Database: {database}")

        # Create directory structure based on pattern
        if pattern == "feature":
            dirs = [
                "app/core",
                "app/features",
                "app/api",
                "app/models",
                "tests",
                "logs"
            ]

            # Add alembic only for SQL databases
            if database != "firebase":
                dirs.append("alembic/versions")

            if not minimal:
                dirs.extend([
                    "app/services",
                    "app/repositories",
                    "app/middleware",
                    "app/dependencies",
                    "database/seeders",
                    "database/factories"
                ])

        elif pattern == "api":
            dirs = [
                "app/core",
                "app/api",
                "app/schemas",
                "app/models",
                "tests",
                "logs"
            ]

            # Add alembic only for SQL databases
            if database != "firebase":
                dirs.append("alembic/versions")

        elif pattern == "layer":
            dirs = [
                "app/core",
                "app/controllers",
                "app/services",
                "app/repositories",
                "app/models",
                "app/schemas",
                "app/middleware",
                "tests",
                "logs"
            ]

            # Add alembic only for SQL databases
            if database != "firebase":
                dirs.append("alembic/versions")

        for dir_path in dirs:
            PathManager.ensure_dir(project_path / dir_path)

        # Generate secret key
        secret_key = secrets.token_urlsafe(32)

        # Context for templates
        ctx = {
            "project_name": name,
            "version": __version__,
            "secret_key": secret_key
        }

        # Select database template
        database_template = self._get_database_template(database)
        database_filename = "firebase.py" if database == "firebase" else "database.py"

        # Write core files
        files = {
            "app/main.py": Templates.MAIN_APP,
            "app/core/config.py": Templates.CONFIG,
            f"app/core/{database_filename}": database_template,
            "app/core/logging.py": Templates.LOGGING,
            "app/core/discovery.py": Templates.DISCOVERY,
            "app/core/graphql.py": Templates.GRAPHQL,
            ".env": self._get_database_env_template(database, name, secret_key),
            ".gitignore": Templates.GITIGNORE,
        }

        # Add alembic files only for SQL databases
        if database != "firebase":
            files["alembic/env.py"] = Templates.ALEMBIC_ENV
            files["alembic.ini"] = Templates.ALEMBIC_INI
        else:
            # Add Firebase credentials example for Firebase projects
            firebase_creds_example = '''{
  "type": "service_account",
  "project_id": "your-project-id",
  "private_key_id": "your-private-key-id",
  "private_key": "-----BEGIN PRIVATE KEY-----\\nYOUR-PRIVATE-KEY\\n-----END PRIVATE KEY-----\\n",
  "client_email": "your-service-account@your-project.iam.gserviceaccount.com",
  "client_id": "your-client-id",
  "auth_uri": "https://accounts.google.com/o/oauth2/auth",
  "token_uri": "https://oauth2.googleapis.com/token",
  "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
  "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/your-service-account%40your-project.iam.gserviceaccount.com"
}'''
            files["firebase-credentials.json.example"] = firebase_creds_example

        for file_path, template in files.items():
            full_path = project_path / file_path
            content = Template.render(template, ctx)
            PathManager.write_file(full_path, content)

        # Create README
        pattern_desc = {
            "feature": "Feature modules (vertical slices)",
            "api": "API-focused structure",
            "layer": "Layered architecture (controllers, services, repositories)"
        }

        readme = f"""# {name}

FastAPI project generated with Fastman v{__version__}

**Pattern**: {pattern} - {pattern_desc[pattern]}
**Package Manager**: {package_manager}

## Getting Started

```bash
cd {name}

# Activate virtual environment (if created)
{"source .venv/bin/activate  # Linux/Mac" if package_manager != "uv" else "# uv handles venv automatically"}
{".\\.venv\\\\Scripts\\\\activate  # Windows" if package_manager != "uv" else ""}

# Install dependencies
{self._get_install_command(package_manager)}

# Run development server
fastman serve

# View available commands
fastman list
```

## Project Structure

```
{name}/
├── app/
│   ├── core/          # Core configuration and utilities
{self._get_structure_docs(pattern)}
├── tests/             # Test files
├── alembic/           # Database migrations
└── logs/              # Application logs
```

## Documentation

- API Documentation: http://localhost:8000/docs
- GraphQL Playground: http://localhost:8000/graphql

Generated with ❤️ by Fastman
"""
        PathManager.write_file(project_path / "README.md", readme)

        # Change to project directory for initialization
        original_dir = os.getcwd()
        os.chdir(project_path)

        try:
            # Get database-specific dependencies
            dependencies = self._get_database_dependencies(database, minimal)

            # Initialize based on package manager
            self._initialize_package_manager(package_manager, dependencies, name)

        finally:
            os.chdir(original_dir)

        Output.success(f"Project '{name}' created successfully!")
        Output.info(f"\nNext steps:")
        Output.echo(f"  cd {name}", Style.CYAN)
        if package_manager == "pipenv":
            Output.echo(f"  pipenv shell", Style.CYAN)
        elif package_manager == "poetry":
            Output.echo(f"  poetry shell", Style.CYAN)
        Output.echo(f"  fastman serve", Style.CYAN)

    def _get_install_command(self, package_manager: str) -> str:
        """Get install command for package manager"""
        commands = {
            "uv": "uv sync",
            "pipenv": "pipenv install",
            "poetry": "poetry install"
        }
        return commands.get(package_manager, "pip install -r requirements.txt")

    def _get_structure_docs(self, pattern: str) -> str:
        """Get structure documentation based on pattern"""
        structures = {
            "feature": """│   ├── features/      # Feature modules (vertical slices)
│   ├── api/           # Lightweight API endpoints
│   └── models/        # Database models""",
            "api": """│   ├── api/           # API endpoints
│   ├── schemas/       # Pydantic schemas
│   └── models/        # Database models""",
            "layer": """│   ├── controllers/   # Request handlers
│   ├── services/      # Business logic
│   ├── repositories/  # Data access layer
│   ├── models/        # Database models
│   └── schemas/       # Pydantic schemas"""
        }
        return structures.get(pattern, "")

    def _initialize_package_manager(self, package_manager: str, dependencies: list, project_name: str):
        """Initialize project with specified package manager"""

        if package_manager == "uv":
            # Check if uv is available
            if not shutil.which("uv"):
                Output.warn("uv not found. Creating requirements.txt instead.")
                self._create_requirements_txt(dependencies)
                return

            Output.info("Initializing with uv...")
            try:
                # Initialize uv project
                subprocess.run(["uv", "init", "--no-readme", "--no-pin-python"],
                             check=True, capture_output=True)

                # Create virtual environment in .venv
                Output.info("Creating virtual environment...")
                subprocess.run(["uv", "venv", ".venv"],
                             check=True, capture_output=True)

                # Add dependencies
                Output.info("Installing dependencies...")
                subprocess.run(["uv", "add"] + dependencies,
                             check=True, capture_output=True)

                Output.success("Virtual environment created at .venv/")
            except subprocess.CalledProcessError as e:
                Output.error(f"uv initialization failed: {e}")
                self._create_requirements_txt(dependencies)

        elif package_manager == "pipenv":
            # Check if pipenv is available
            if not shutil.which("pipenv"):
                Output.warn("pipenv not found. Installing...")
                subprocess.run([sys.executable, "-m", "pip", "install", "pipenv"],
                             capture_output=True)

            Output.info("Initializing with pipenv...")
            try:
                # Set environment variable to create venv in project
                env = os.environ.copy()
                env["PIPENV_VENV_IN_PROJECT"] = "1"

                # Install dependencies (creates .venv in project)
                subprocess.run(["pipenv", "install"] + dependencies,
                             env=env, check=True, capture_output=True)

                Output.success("Virtual environment created at .venv/")
            except subprocess.CalledProcessError as e:
                Output.error(f"pipenv initialization failed: {e}")
                self._create_requirements_txt(dependencies)

        elif package_manager == "poetry":
            # Check if poetry is available
            if not shutil.which("poetry"):
                Output.warn("poetry not found. Please install poetry first.")
                self._create_requirements_txt(dependencies)
                return

            Output.info("Initializing with poetry...")
            try:
                # Configure poetry to create venv in project
                subprocess.run(["poetry", "config", "virtualenvs.in-project", "true"],
                             capture_output=True)

                # Initialize poetry project
                subprocess.run(["poetry", "init", "--no-interaction",
                              f"--name={project_name}",
                              "--python=^3.9"],
                             check=True, capture_output=True)

                # Add dependencies
                subprocess.run(["poetry", "add"] + dependencies,
                             check=True, capture_output=True)

                Output.success("Virtual environment created at .venv/")
            except subprocess.CalledProcessError as e:
                Output.error(f"poetry initialization failed: {e}")
                self._create_requirements_txt(dependencies)

    def _get_database_template(self, database: str) -> str:
        """Get database configuration template based on database type"""
        templates = {
            "sqlite": Templates.DATABASE,
            "postgresql": Templates.DATABASE_POSTGRESQL,
            "mysql": Templates.DATABASE_MYSQL,
            "oracle": Templates.DATABASE_ORACLE,
            "firebase": Templates.DATABASE_FIREBASE
        }
        return templates.get(database, Templates.DATABASE)

    def _get_database_env_template(self, database: str, project_name: str, secret_key: str) -> str:
        """Get database-specific environment variables"""

        base_env = f"""# Application
PROJECT_NAME={project_name}
ENVIRONMENT=development
DEBUG=true
SECRET_KEY={secret_key}

# API
API_V1_PREFIX=/api/v1
ALLOWED_HOSTS=["*"]
"""

        database_configs = {
            "sqlite": """
# Database
DATABASE_URL=sqlite:///./app.db
""",
            "postgresql": f"""
# Database (PostgreSQL)
# IMPORTANT: Replace placeholders with your actual database credentials
DATABASE_URL=postgresql://<YOUR_USER>:<YOUR_PASSWORD>@localhost:5432/{project_name}
POSTGRES_USER=<YOUR_USER>
POSTGRES_PASSWORD=<YOUR_PASSWORD>
POSTGRES_DB={project_name}
""",
            "mysql": f"""
# Database (MySQL)
# IMPORTANT: Replace placeholders with your actual database credentials
DATABASE_URL=mysql+pymysql://<YOUR_USER>:<YOUR_PASSWORD>@localhost:3306/{project_name}
MYSQL_USER=<YOUR_USER>
MYSQL_PASSWORD=<YOUR_PASSWORD>
MYSQL_DATABASE={project_name}
""",
            "oracle": f"""
# Database (Oracle)
# IMPORTANT: Replace placeholders with your actual database credentials
DATABASE_URL=oracle+cx_oracle://<YOUR_USER>:<YOUR_PASSWORD>@localhost:1521/XE
ORACLE_USER=<YOUR_USER>
ORACLE_PASSWORD=<YOUR_PASSWORD>
ORACLE_SID=XE
""",
            "firebase": f"""
# Firebase
FIREBASE_PROJECT_ID=your-project-id
FIREBASE_CREDENTIALS_PATH=./firebase-credentials.json
"""
        }

        return base_env + database_configs.get(database, database_configs["sqlite"])

    def _get_database_dependencies(self, database: str, minimal: bool) -> list:
        """Get database-specific dependencies"""

        # Base dependencies (always included)
        base_deps = [
            "fastapi",
            "uvicorn[standard]",
            "pydantic-settings",
            "python-dotenv"
        ]

        # Database-specific dependencies
        if database == "sqlite":
            base_deps.extend(["sqlalchemy", "alembic"])
        elif database == "postgresql":
            base_deps.extend(["sqlalchemy", "alembic", "psycopg2-binary"])
        elif database == "mysql":
            base_deps.extend(["sqlalchemy", "alembic", "pymysql"])
        elif database == "oracle":
            base_deps.extend(["sqlalchemy", "alembic", "cx_Oracle"])
        elif database == "firebase":
            base_deps.append("firebase-admin")

        # Optional dependencies (if not minimal)
        if not minimal:
            base_deps.extend([
                "strawberry-graphql[fastapi]",
                "faker",
                "pytest",
                "httpx"
            ])

        return base_deps

    def _create_requirements_txt(self, dependencies: list):
        """Fallback: create requirements.txt"""
        req_file = Path("requirements.txt")
        req_file.write_text("\n".join(dependencies))
        Output.info("Created requirements.txt")
        Output.info("Run: python -m venv .venv && pip install -r requirements.txt")

@register
class InitCommand(Command):
    signature = "init"
    description = "Initialize Fastman in existing project"

    def handle(self):
        if not Output.confirm("Initialize Fastman in current directory?"):
            Output.info("Cancelled")
            return

        Output.info("Initializing Fastman...")

        # Create necessary directories
        dirs = [
            "app/console/commands",
            "app/core",
            "app/features",
            "app/api"
        ]

        for dir_path in dirs:
            PathManager.ensure_dir(Path(dir_path))

        # Create basic files if they don't exist
        files_to_create = {
            ".env": "# Environment variables\n",
            ".gitignore": Templates.GITIGNORE,
        }

        for file_path, content in files_to_create.items():
            path = Path(file_path)
            if not path.exists():
                PathManager.write_file(path, content)

        Output.success("Fastman initialized!")
        Output.info("Run 'fastman list' to see available commands")
