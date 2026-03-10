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
    signature = "new {name} {--minimal} {--pattern=feature} {--package=uv} {--database=sqlite} {--graphql}"
    description = "Create a new FastAPI project"
    help = """
Examples:
  fastman new my_api --pattern=api
  fastman new my_proj --database=postgresql --graphql
  fastman new my_feature --pattern=feature
"""

    def handle(self):
        name = self.argument(0)
        if not name:
            raise ValueError("Project name is required")
        NameValidator.validate_path_component(name)

        minimal = self.flag("minimal")
        pattern = self.option("pattern", "feature").lower()
        package_manager = self.option("package", "uv").lower()
        database = self.option("database", "sqlite").lower()
        graphql = self.flag("graphql")

        # Validate pattern
        valid_patterns = ["feature", "api", "layer"]
        if pattern not in valid_patterns:
            Output.error(f"Invalid pattern '{pattern}'. Must be one of: {', '.join(valid_patterns)}")
            return

        # Validate package manager
        valid_packages = ["uv", "pipenv", "poetry", "pip"]
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
            sys.exit(1)

        Output.banner(__version__)
        Output.section("Creating Project", f"{name} ({pattern} pattern with {database}{' + GraphQL' if graphql else ''})")
        
        progress, task_id = Output.start_progress(f"Scaffolding {name}...")
        if progress: progress.update(task_id, description="Setting up project directories...", advance=10)
        
        if pattern == "feature":
            dirs = [
                "app/core",
                "app/features",
                "app/models",
                "tests",
                "logs"
            ]
            # Add alembic only for SQL databases
            if database != "firebase":
                dirs.append("alembic/versions")

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
            "config_db_fields": self._get_config_db_fields(database),
            "project_name": name,
            "version": __version__,
            "secret_key": secret_key,
        }

        # Select database template
        database_template = self._get_database_template(database)
        database_filename = "firebase.py" if database == "firebase" else "database.py"

        # Generate env files for all environments
        env_files = self._get_env_files(database, name, secret_key)

        # Write core files
        files = {
            "app/main.py": Templates.MAIN_APP,
            "app/core/config.py": Templates.CONFIG,
            f"app/core/{database_filename}": database_template,
            "app/core/logging.py": Templates.LOGGING,
            "app/core/discovery.py": Templates.DISCOVERY,
            ".gitignore": Templates.GITIGNORE,
        }

        # Add all env files
        files.update(env_files)

        # Add GraphQL file only if requested
        if graphql:
            files["app/core/graphql.py"] = Templates.GRAPHQL

        # Add alembic files only for SQL databases
        if database != "firebase":
            files["alembic/env.py"] = Templates.ALEMBIC_ENV
            files["alembic.ini"] = Templates.ALEMBIC_INI
            files["alembic/script.py.mako"] = Templates.ALEMBIC_SCRIPT_MAKO
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

        if progress: progress.update(task_id, description="Generating core templates...", advance=20)
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

        # Prepare activation strings to avoid backslash syntax errors in f-string
        linux_activate = "source .venv/bin/activate  # Linux/Mac"
        windows_activate = ".\\.venv\\Scripts\\activate  # Windows"
        uv_note = "# uv handles venv automatically"

        activation_linux = linux_activate if package_manager != "uv" else uv_note
        activation_windows = windows_activate if package_manager != "uv" else uv_note

        readme = f"""# {name}

FastAPI project generated with Fastman v{__version__}

**Pattern**: {pattern} - {pattern_desc[pattern]}
**Package Manager**: {package_manager}

## Getting Started

```bash
cd {name}

# Activate virtual environment (if created)
{activation_linux}
{activation_windows}

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
{self._get_alembic_docs(database)}
└── logs/              # Application logs
```

## Documentation

- API Documentation: http://localhost:8000/docs
{"- GraphQL Playground: http://localhost:8000/graphql" if graphql else ""}

Generated with ❤️ by Fastman
"""
        PathManager.write_file(project_path / "README.md", readme)

        dependencies = self._get_database_dependencies(database, graphql, minimal)
        self._initialize_package_manager(package_manager, dependencies, name, project_path, progress, task_id)

        Output.stop_progress(progress)

        Output.line()
        Output.success(f"Project '{name}' created successfully!", icon=True)
        
        steps = [(f"cd {name}", "Navigate to project directory")]
        if package_manager == "pipenv":
            steps.append(("pipenv shell", "Activate pipenv environment"))
        elif package_manager == "poetry":
            steps.append(("poetry shell", "Activate poetry environment"))
        elif package_manager == "pip":
            steps.append(("source .venv/bin/activate", "Activate virtual environment (Linux/Mac)"))
            steps.append((".\\.venv\\Scripts\\activate", "Activate virtual environment (Windows)"))
        
        steps.extend([
            ("fastman serve", "Start the development server"),
            ("fastman list", "View all available commands"),
        ])
        
        Output.next_steps(steps)

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
│   └── models/        # Shared database models""",
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

    def _get_alembic_docs(self, database: str) -> str:
        """Get alembic documentation line if applicable"""
        if database == "firebase":
            return ""
        return "├── alembic/           # Database migrations"

    def _initialize_package_manager(self, package_manager: str, dependencies: list, project_name: str, cwd: Path = None, progress=None, task_id=None):
        """Initialize project with specified package manager"""
        
        if progress: progress.update(task_id, description=f"Initializing {package_manager}...", advance=10)
        
        if package_manager == "uv":
            if not shutil.which("uv"):
                Output.warn("uv not found. Falling back to requirements.txt")
                self._create_requirements_txt(dependencies, cwd=cwd)
                return

            try:
                subprocess.run(["uv", "init", "--no-readme", "--no-pin-python"],
                             check=True, capture_output=True, timeout=60, cwd=cwd)

                subprocess.run(["uv", "venv", ".venv"],
                             check=True, capture_output=True, timeout=120, cwd=cwd)

                subprocess.run(["uv", "add"] + dependencies,
                             check=True, capture_output=True, timeout=300, cwd=cwd)

                if progress: progress.update(task_id, description="Virtual environment created", advance=50)
            except subprocess.TimeoutExpired:
                Output.error("uv initialization timed out. Try again with a faster connection.")
                self._create_requirements_txt(dependencies, cwd=cwd)
            except subprocess.CalledProcessError as e:
                Output.error(f"uv initialization failed: {e}")
                self._create_requirements_txt(dependencies, cwd=cwd)

        elif package_manager == "pipenv":
            if not shutil.which("pipenv"):
                try:
                    subprocess.run([sys.executable, "-m", "pip", "install", "pipenv"],
                                 capture_output=True, check=True, timeout=60)
                except subprocess.TimeoutExpired:
                    Output.error("pipenv installation timed out. Please install pipenv manually.")
                    return
                except subprocess.CalledProcessError as e:
                    Output.error(f"Failed to install pipenv: {e}")
                    return

            try:
                env = os.environ.copy()
                env["PIPENV_VENV_IN_PROJECT"] = "1"

                subprocess.run(["pipenv", "install"] + dependencies,
                             env=env, check=True, capture_output=True, timeout=300, cwd=cwd)

                if progress: progress.update(task_id, description="Virtual environment created", advance=50)
            except subprocess.TimeoutExpired:
                Output.error("pipenv initialization timed out. Try again with a faster connection.")
                self._create_requirements_txt(dependencies, cwd=cwd)
            except subprocess.CalledProcessError as e:
                Output.error(f"pipenv initialization failed: {e}")
                self._create_requirements_txt(dependencies, cwd=cwd)

        elif package_manager == "poetry":
            if not shutil.which("poetry"):
                Output.warn("poetry not found. Falling back to requirements.txt")
                self._create_requirements_txt(dependencies, cwd=cwd)
                return

            try:
                try:
                    subprocess.run(["poetry", "config", "virtualenvs.in-project", "true"],
                                 capture_output=True, check=True, timeout=30, cwd=cwd)
                except subprocess.CalledProcessError as e:
                    Output.warn(f"Could not configure virtualenvs.in-project: {e}")

                subprocess.run(["poetry", "init", "--no-interaction",
                              f"--name={project_name}",
                              "--python=^3.9"],
                             check=True, capture_output=True, timeout=60, cwd=cwd)

                subprocess.run(["poetry", "add"] + dependencies,
                             check=True, capture_output=True, timeout=300, cwd=cwd)

                if progress: progress.update(task_id, description="Virtual environment created", advance=50)
            except subprocess.TimeoutExpired:
                Output.error("poetry initialization timed out. Try again with a faster connection.")
                self._create_requirements_txt(dependencies, cwd=cwd)
            except subprocess.CalledProcessError as e:
                Output.error(f"poetry initialization failed: {e}")
                self._create_requirements_txt(dependencies, cwd=cwd)

        elif package_manager == "pip":
            try:
                subprocess.run([sys.executable, "-m", "venv", ".venv"], check=True, timeout=120, cwd=cwd)

                self._create_requirements_txt(dependencies, cwd=cwd)

                pip_path = str(cwd.resolve() / ".venv" / "bin" / "pip") if os.name != "nt" else str(cwd.resolve() / ".venv" / "Scripts" / "pip.exe")
                subprocess.run([pip_path, "install", "-r", "requirements.txt"], check=True, timeout=300, cwd=cwd)

                if progress: progress.update(task_id, description="Virtual environment created", advance=50)
            except subprocess.TimeoutExpired:
                Output.error("pip initialization timed out. Try again with a faster connection.")
            except subprocess.CalledProcessError as e:
                Output.error(f"pip initialization failed: {e}")

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
        """Get database-specific environment variables for a single env file"""

        base_env = f"""# Application
PROJECT_NAME={project_name}
ENVIRONMENT={{environment}}
DEBUG={{debug}}
SECRET_KEY={secret_key}

# API
API_V1_PREFIX=/api/v1
ALLOWED_HOSTS={{allowed_hosts}}
"""

        database_configs = {
            "sqlite": """
# Database
DATABASE_URL=sqlite:///./app.db
""",
            "postgresql": f"""
# Database (PostgreSQL)
DB_HOST={{db_host}}
DB_PORT=5432
DB_USER={{db_user}}
DB_PASSWORD={{db_password}}
DB_NAME={project_name}
DATABASE_URL=postgresql://{{db_user}}:{{db_password}}@{{db_host}}:5432/{project_name}
""",
            "mysql": f"""
# Database (MySQL)
DB_HOST={{db_host}}
DB_PORT=3306
DB_USER={{db_user}}
DB_PASSWORD={{db_password}}
DB_NAME={project_name}
DATABASE_URL=mysql+pymysql://{{db_user}}:{{db_password}}@{{db_host}}:3306/{project_name}
""",
            "oracle": """
# Database (Oracle)
DB_HOST={db_host}
DB_PORT=1521
DB_USER={db_user}
DB_PASSWORD={db_password}
DB_NAME=XE
DATABASE_URL=oracle+oracledb://{db_user}:{db_password}@{db_host}:1521/XE
""",
            "firebase": """
# Firebase
FIREBASE_PROJECT_ID=your-project-id
FIREBASE_CREDENTIALS_PATH=./firebase-credentials.json
"""
        }

        return base_env + database_configs.get(database, database_configs["sqlite"])

    def _get_env_files(self, database: str, project_name: str, secret_key: str) -> dict:
        """Generate all environment files (dev, staging, production)"""
        environments = {
            ".env": {
                "environment": "development",
                "debug": "true",
                "allowed_hosts": '["*"]',
                "db_host": "localhost",
                "db_user": "<YOUR_USER>",
                "db_password": "<YOUR_PASSWORD>",
            },
            ".env.development": {
                "environment": "development",
                "debug": "true",
                "allowed_hosts": '["*"]',
                "db_host": "localhost",
                "db_user": "<YOUR_USER>",
                "db_password": "<YOUR_PASSWORD>",
            },
            ".env.staging": {
                "environment": "staging",
                "debug": "true",
                "allowed_hosts": '["*"]',
                "db_host": "staging-db-host",
                "db_user": "<STAGING_USER>",
                "db_password": "<STAGING_PASSWORD>",
            },
            ".env.production": {
                "environment": "production",
                "debug": "false",
                "allowed_hosts": '["https://yourdomain.com"]',
                "db_host": "production-db-host",
                "db_user": "<PROD_USER>",
                "db_password": "<PROD_PASSWORD>",
            },
        }

        env_files = {}
        template = self._get_database_env_template(database, project_name, secret_key)
        for filename, values in environments.items():
            content = template
            for key, value in values.items():
                content = content.replace("{" + key + "}", value)
            env_files[filename] = content

        return env_files

    def _get_config_db_fields(self, database: str) -> str:
        """Get database-specific config fields for the Settings class"""
        fields = {
            "sqlite": """# Database
    DATABASE_URL: Optional[str] = "sqlite:///./app.db"
""",
            "postgresql": """# Database (PostgreSQL)
    DB_HOST: str = "localhost"
    DB_PORT: int = 5432
    DB_USER: str = "postgres"
    DB_PASSWORD: str = ""
    DB_NAME: str = "{project_name}"
    DATABASE_URL: Optional[str] = None

    @computed_field
    @property
    def database_url(self) -> str:
        if self.DATABASE_URL:
            return self.DATABASE_URL
        return f"postgresql://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
""",
            "mysql": """# Database (MySQL)
    DB_HOST: str = "localhost"
    DB_PORT: int = 3306
    DB_USER: str = "root"
    DB_PASSWORD: str = ""
    DB_NAME: str = "{project_name}"
    DATABASE_URL: Optional[str] = None

    @computed_field
    @property
    def database_url(self) -> str:
        if self.DATABASE_URL:
            return self.DATABASE_URL
        return f"mysql+pymysql://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
""",
            "oracle": """# Database (Oracle)
    DB_HOST: str = "localhost"
    DB_PORT: int = 1521
    DB_USER: str = "system"
    DB_PASSWORD: str = ""
    DB_NAME: str = "XE"
    DATABASE_URL: Optional[str] = None

    @computed_field
    @property
    def database_url(self) -> str:
        if self.DATABASE_URL:
            return self.DATABASE_URL
        return f"oracle+oracledb://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
""",
            "firebase": """# Firebase (NoSQL)
    FIREBASE_PROJECT_ID: Optional[str] = None
    FIREBASE_CREDENTIALS_PATH: Optional[str] = None
""",
        }
        return fields.get(database, fields["sqlite"])

    def _get_database_dependencies(self, database: str, graphql: bool = False, minimal: bool = False) -> list:
        """Get database-specific dependencies"""

        # Base dependencies (always included)
        base_deps = [
            "fastapi",
            "uvicorn[standard]",
            "pydantic-settings",
            "python-dotenv",
            "pydantic[email]"
        ]

        # Database-specific dependencies (unless minimal)
        if not minimal:
            if database == "sqlite":
                base_deps.extend(["sqlalchemy", "alembic"])
            elif database == "postgresql":
                base_deps.extend(["sqlalchemy", "alembic", "psycopg2-binary"])
            elif database == "mysql":
                base_deps.extend(["sqlalchemy", "alembic", "pymysql"])
            elif database == "oracle":
                base_deps.extend(["sqlalchemy", "alembic", "oracledb"])
            elif database == "firebase":
                base_deps.append("firebase-admin")

        # Dev dependencies (unless minimal)
        if not minimal:
            base_deps.extend([
                "faker",
                "pytest",
                "httpx"
            ])

        # Add GraphQL dependency only if requested
        if graphql:
            base_deps.append("strawberry-graphql[fastapi]")

        return base_deps

    def _create_requirements_txt(self, dependencies: list, cwd: Path = None):
        """Fallback: create requirements.txt"""
        req_file = (cwd or Path.cwd()) / "requirements.txt"
        req_file.write_text("\n".join(dependencies) + "\n")
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

        # Create necessary directories (feature pattern by default)
        dirs = [
            "app/console/commands",
            "app/core",
            "app/features",
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
