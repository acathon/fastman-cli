#!/usr/bin/env python3
"""
Fastman - The Complete FastAPI CLI Framework
Version: 0.1.0
License: MIT
Author: Fastman Contributors
Repository: https://github.com/fastman/fastman

A Fastman CLI for FastAPI that makes building APIs a breeze.
"""

import sys
import os
import shutil
import subprocess
import re
import pkgutil
import importlib
import secrets
import json
import logging
from pathlib import Path
from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any, Callable
from dataclasses import dataclass
from enum import Enum

__version__ = "0.1.0"

# ============================================================================
# DEPENDENCIES & CONFIGURATION
# ============================================================================

try:
    import pyfiglet
    HAS_PYFIGLET = True
except ImportError:
    HAS_PYFIGLET = False

try:
    from rich.console import Console
    from rich.table import Table
    from rich.progress import Progress, SpinnerColumn, TextColumn
    from rich.panel import Panel
    from rich.prompt import Confirm
    HAS_RICH = True
    console = Console()
except ImportError:
    HAS_RICH = False
    console = None

# Logging setup
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('fastman')


# ============================================================================
# STYLES & OUTPUT
# ============================================================================

class Style:
    """ANSI color codes for terminal output"""
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    RESET = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


class OutputLevel(Enum):
    """Output verbosity levels"""
    SUCCESS = "success"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    DEBUG = "debug"


class Output:
    """Handles all CLI output with fallback support"""
    
    @staticmethod
    def echo(msg: str, style: str = ""):
        """Basic echo with style"""
        if HAS_RICH and console:
            console.print(msg)
        else:
            print(f"{style}{msg}{Style.RESET}")
    
    @staticmethod
    def success(msg: str):
        """Success message"""
        if HAS_RICH:
            try:
                console.print(f"[green]✔[/green] {msg}")
            except UnicodeEncodeError:
                print(f"{Style.GREEN}[OK] {msg}{Style.RESET}")
        else:
            try:
                print(f"{Style.GREEN}✔ {msg}{Style.RESET}")
            except UnicodeEncodeError:
                print(f"{Style.GREEN}[OK] {msg}{Style.RESET}")
        logger.info(msg)
    
    @staticmethod
    def info(msg: str):
        """Info message"""
        if HAS_RICH:
            try:
                console.print(f"[blue]ℹ[/blue] {msg}")
            except UnicodeEncodeError:
                print(f"{Style.BLUE}[INFO] {msg}{Style.RESET}")
        else:
            try:
                print(f"{Style.BLUE}ℹ {msg}{Style.RESET}")
            except UnicodeEncodeError:
                print(f"{Style.BLUE}[INFO] {msg}{Style.RESET}")
        logger.info(msg)
    
    @staticmethod
    def warn(msg: str):
        """Warning message"""
        if HAS_RICH:
            try:
                console.print(f"[yellow]⚠[/yellow] {msg}")
            except UnicodeEncodeError:
                print(f"{Style.YELLOW}[WARN] {msg}{Style.RESET}")
        else:
            try:
                print(f"{Style.YELLOW}⚠ {msg}{Style.RESET}")
            except UnicodeEncodeError:
                print(f"{Style.YELLOW}[WARN] {msg}{Style.RESET}")
        logger.warning(msg)
    
    @staticmethod
    def error(msg: str):
        """Error message"""
        if HAS_RICH:
            try:
                console.print(f"[red]✖[/red] {msg}")
            except UnicodeEncodeError:
                print(f"{Style.RED}[ERROR] {msg}{Style.RESET}")
        else:
            try:
                print(f"{Style.RED}✖ {msg}{Style.RESET}")
            except UnicodeEncodeError:
                print(f"{Style.RED}[ERROR] {msg}{Style.RESET}")
        logger.error(msg)
    
    @staticmethod
    def banner():
        """Display application banner"""
        if HAS_PYFIGLET:
            banner_text = pyfiglet.figlet_format("Fastman", font="slant")
        else:
            banner_text = """
    ███████╗ █████╗ ███████╗████████╗███╗   ███╗ █████╗ ███╗   ██╗
    ██╔════╝██╔══██╗██╔════╝╚══██╔══╝████╗ ████║██╔══██╗████╗  ██║
    █████╗  ███████║███████╗   ██║   ██╔████╔██║███████║██╔██╗ ██║
    ██╔══╝  ██╔══██║╚════██║   ██║   ██║╚██╔╝██║██╔══██║██║╚██╗██║
    ██║     ██║  ██║███████║   ██║   ██║ ╚═╝ ██║██║  ██║██║ ╚████║
    ╚═╝     ╚═╝  ╚═╝╚══════╝   ╚═╝   ╚═╝     ╚═╝╚═╝  ╚═╝╚═╝  ╚═══╝
            """
        
        if HAS_RICH:
            console.print(Panel(
                banner_text,
                title=f"[bold cyan]Fastman v{__version__}[/bold cyan]",
                subtitle="The Complete FastAPI CLI",
                border_style="cyan"
            ))
        else:
            Output.echo(banner_text, Style.CYAN)
            Output.echo(f"Version {__version__} - The Complete FastAPI CLI\n", Style.BOLD)
    
    @staticmethod
    def table(headers: List[str], rows: List[List[str]], title: str = None):
        """Display data in table format"""
        if HAS_RICH:
            table = Table(title=title, show_header=True, header_style="bold cyan")
            for header in headers:
                table.add_column(header)
            for row in rows:
                table.add_row(*row)
            console.print(table)
        else:
            if title:
                Output.echo(f"\n{title}", Style.BOLD)
            Output.echo("-" * 80)
            Output.echo(" | ".join(headers), Style.CYAN)
            Output.echo("-" * 80)
            for row in rows:
                print(" | ".join(row))
            Output.echo("-" * 80)
    
    @staticmethod
    def confirm(message: str, default: bool = False) -> bool:
        """Ask for user confirmation"""
        if HAS_RICH:
            return Confirm.ask(message, default=default)
        else:
            default_str = "Y/n" if default else "y/N"
            response = input(f"{message} [{default_str}]: ").strip().lower()
            if not response:
                return default
            return response in ['y', 'yes']


# ============================================================================
# UTILITIES & HELPERS
# ============================================================================

class NameValidator:
    """Validates and sanitizes names"""
    
    @staticmethod
    def validate_identifier(name: str) -> str:
        """Validate Python identifier"""
        if not name:
            raise ValueError("Name cannot be empty")
        
        if not re.match(r'^[a-zA-Z][a-zA-Z0-9_]*$', name):
            raise ValueError(
                f"Invalid name '{name}'. Must start with letter and contain only letters, numbers, underscores"
            )
        
        return name
    
    @staticmethod
    def validate_path_component(name: str) -> str:
        """Validate path component (no traversal)"""
        if not name:
            raise ValueError("Name cannot be empty")
        
        if '..' in name or '/' in name or '\\' in name:
            raise ValueError(f"Invalid name '{name}'. Cannot contain path separators")
        
        return name
    
    @staticmethod
    def to_snake_case(name: str) -> str:
        """Convert to snake_case"""
        name = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
        name = re.sub('([a-z0-9])([A-Z])', r'\1_\2', name)
        return name.lower().strip('_')
    
    @staticmethod
    def to_pascal_case(name: str) -> str:
        """Convert to PascalCase"""
        parts = NameValidator.to_snake_case(name).split('_')
        return ''.join(word.capitalize() for word in parts if word)
    
    @staticmethod
    def to_kebab_case(name: str) -> str:
        """Convert to kebab-case"""
        return NameValidator.to_snake_case(name).replace('_', '-')


class PathManager:
    """Manages file system operations safely"""
    
    @staticmethod
    def ensure_dir(path: Path) -> Path:
        """Create directory and __init__.py if needed"""
        path.mkdir(parents=True, exist_ok=True)
        
        init_file = path / "__init__.py"
        if not init_file.exists():
            init_file.touch()
        
        return path
    
    @staticmethod
    def write_file(path: Path, content: str, overwrite: bool = False) -> bool:
        """Write file with safety checks"""
        try:
            with path.open('x' if not overwrite else 'w', encoding='utf-8') as f:
                f.write(content)
            return True
        except FileExistsError:
            Output.warn(f"File already exists: {path}")
            return False
        
        path.parent.mkdir(parents=True, exist_ok=True)
        
        try:
            path.write_text(content, encoding='utf-8')
            return True
        except Exception as e:
            Output.error(f"Failed to write {path}: {e}")
            logger.exception(e)
            return False
    
    @staticmethod
    def safe_remove(path: Path) -> bool:
        """Safely remove file or directory"""
        try:
            if path.is_file():
                path.unlink()
            elif path.is_dir():
                shutil.rmtree(path)
            return True
        except Exception as e:
            Output.error(f"Failed to remove {path}: {e}")
            return False


class PackageManager:
    """Handles package management across different tools"""
    
    @staticmethod
    def detect() -> tuple[str, List[str]]:
        """Detect package manager and return (name, run_prefix)"""
        cwd = Path.cwd()
        
        if (cwd / "uv.lock").exists() or (shutil.which("uv") and (cwd / "pyproject.toml").exists()):
            return ("uv", ["uv", "run"])
        
        if (cwd / "poetry.lock").exists():
            return ("poetry", ["poetry", "run"])
        
        if (cwd / "Pipfile").exists():
            return ("pipenv", ["pipenv", "run"])
        
        return ("pip", [])
    
    @staticmethod
    def install(packages: List[str]) -> bool:
        """Install packages using detected package manager"""
        if not packages:
            return True
        
        manager, _ = PackageManager.detect()
        
        try:
            if manager == "uv":
                subprocess.run(["uv", "add"] + packages, check=True)
            elif manager == "poetry":
                subprocess.run(["poetry", "add"] + packages, check=True)
            elif manager == "pipenv":
                subprocess.run(["pipenv", "install"] + packages, check=True)
            else:
                subprocess.run([sys.executable, "-m", "pip", "install"] + packages, check=True)
                
                # Update requirements.txt
                req_file = Path("requirements.txt")
                if req_file.exists():
                    existing = req_file.read_text().splitlines()
                    for pkg in packages:
                        if pkg not in existing:
                            with req_file.open("a") as f:
                                f.write(f"\n{pkg}")
            
            return True
        except subprocess.CalledProcessError as e:
            Output.error(f"Package installation failed: {e}")
            return False
    
    @staticmethod
    def get_run_prefix() -> List[str]:
        """Get command prefix for running scripts"""
        _, prefix = PackageManager.detect()
        return prefix


# ============================================================================
# TEMPLATE ENGINE
# ============================================================================

class Template:
    """Simple template engine with variable substitution"""
    
    @staticmethod
    def render(template: str, context: Dict[str, Any]) -> str:
        """Render template with context variables"""
        result = template
        for key, value in context.items():
            # result = re.sub(f"\\{{{key}\\}}", str(value), result)
            result = result.replace(f"{{{key}}}", str(value))
        return result


class Templates:
    """Repository of all code templates"""
    
    MAIN_APP = '''"""
{project_name} - FastAPI Application
Generated by Fastman v{version}
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.core.logging import setup_logging

# Setup logging
setup_logging()

# Initialize FastAPI
app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_HOSTS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Health check
@app.get("/health")
async def health_check():
    return {
        "status": "ok",
        "version": settings.VERSION,
        "environment": settings.ENVIRONMENT
    }

# Auto-discover and include routers
from app.core.discovery import discover_routers
discover_routers(app)

# GraphQL (optional)
try:
    from app.core.graphql import setup_graphql
    setup_graphql(app)
except ImportError:
    pass
'''

    CONFIG = '''"""Application configuration"""
from pydantic_settings import BaseSettings
from typing import List, Optional

class Settings(BaseSettings):
    """Application settings"""
    
    # Project
    PROJECT_NAME: str = "{project_name}"
    VERSION: str = "1.0.0"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    
    # Security
    SECRET_KEY: str = "{secret_key}"
    ALLOWED_HOSTS: List[str] = ["*"]
    
    # Database (SQL)
    DATABASE_URL: Optional[str] = "sqlite:///./app.db"
    
    # Firebase (NoSQL)
    FIREBASE_PROJECT_ID: Optional[str] = None
    FIREBASE_CREDENTIALS_PATH: Optional[str] = None
    
    # API
    API_V1_PREFIX: str = "/api/v1"
    
    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()
'''

    DATABASE = '''"""Database configuration and session management"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base, Session
from typing import Generator
from app.core.config import settings

# Create engine
engine = create_engine(
    settings.DATABASE_URL,
    connect_args={"check_same_thread": False} if settings.DATABASE_URL.startswith("sqlite") else {},
    pool_pre_ping=True,
    echo=settings.DEBUG
)

# Session factory
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

# Base class for models
Base = declarative_base()

def get_db() -> Generator[Session, None, None]:
    """Dependency for database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    """Initialize database tables"""
    Base.metadata.create_all(bind=engine)
'''

    DATABASE_POSTGRESQL = '''"""PostgreSQL database configuration and session management"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base, Session
from typing import Generator
from app.core.config import settings

# Create engine with PostgreSQL-specific settings
engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
    pool_recycle=3600,
    echo=settings.DEBUG
)

# Session factory
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

# Base class for models
Base = declarative_base()

def get_db() -> Generator[Session, None, None]:
    """Dependency for database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    """Initialize database tables"""
    Base.metadata.create_all(bind=engine)
'''

    DATABASE_MYSQL = '''"""MySQL database configuration and session management"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base, Session
from typing import Generator
from app.core.config import settings

# Create engine with MySQL-specific settings
engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
    pool_recycle=3600,
    echo=settings.DEBUG
)

# Session factory
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

# Base class for models
Base = declarative_base()

def get_db() -> Generator[Session, None, None]:
    """Dependency for database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    """Initialize database tables"""
    Base.metadata.create_all(bind=engine)
'''

    DATABASE_ORACLE = '''"""Oracle database configuration and session management"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base, Session
from typing import Generator
from app.core.config import settings

# Create engine with Oracle-specific settings
engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
    pool_recycle=3600,
    echo=settings.DEBUG
)

# Session factory
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

# Base class for models
Base = declarative_base()

def get_db() -> Generator[Session, None, None]:
    """Dependency for database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    """Initialize database tables"""
    Base.metadata.create_all(bind=engine)
'''

    DATABASE_FIREBASE = '''"""Firebase configuration and Firestore access"""
import firebase_admin
from firebase_admin import credentials, firestore
from typing import Optional
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

# Initialize Firebase Admin SDK
_db: Optional[firestore.Client] = None

def init_firebase():
    """Initialize Firebase Admin SDK"""
    global _db
    
    if _db is not None:
        return _db
    
    try:
        # Initialize with credentials
        cred = credentials.Certificate(settings.FIREBASE_CREDENTIALS_PATH)
        firebase_admin.initialize_app(cred, {
            'projectId': settings.FIREBASE_PROJECT_ID,
        })
        
        _db = firestore.client()
        logger.info("Firebase initialized successfully")
        return _db
    except Exception as e:
        logger.error(f"Failed to initialize Firebase: {e}")
        raise

def get_db() -> firestore.Client:
    """Get Firestore client instance"""
    global _db
    
    if _db is None:
        _db = init_firebase()
    
    return _db

# Collection helpers
class Collections:
    """Firestore collection names"""
    USERS = "users"
    # Add more collections as needed
'''

    LOGGING = '''"""Logging configuration"""
import logging
import sys
from pathlib import Path

def setup_logging(log_level: str = "INFO"):
    """Setup application logging"""
    
    # Create logs directory
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    # Configure logging
    logging.basicConfig(
        level=getattr(logging, log_level),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler(log_dir / "app.log")
        ]
    )
    
    # Set third-party loggers to WARNING
    logging.getLogger("uvicorn").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy").setLevel(logging.WARNING)
'''

    DISCOVERY = '''"""Auto-discovery of routers and features"""
import pkgutil
import importlib
from pathlib import Path
from fastapi import FastAPI, APIRouter
import logging

logger = logging.getLogger(__name__)

def discover_routers(app: FastAPI):
    """Discover and register all routers"""
    
    # Feature routers
    features_path = Path("app/features")
    if features_path.exists():
        for item in features_path.iterdir():
            if item.is_dir() and not item.name.startswith("_"):
                router_path = item / "router.py"
                if router_path.exists():
                    try:
                        module = importlib.import_module(f"app.features.{item.name}.router")
                        if hasattr(module, "router"):
                            app.include_router(module.router)
                            logger.info(f"Registered feature router: {item.name}")
                    except Exception as e:
                        logger.error(f"Failed to load feature {item.name}: {e}")
    
    # API routers
    api_path = Path("app/api")
    if api_path.exists():
        for item in api_path.iterdir():
            if item.is_dir() and not item.name.startswith("_"):
                router_path = item / "router.py"
                if router_path.exists():
                    try:
                        module = importlib.import_module(f"app.api.{item.name}.router")
                        if hasattr(module, "router"):
                            app.include_router(module.router)
                            logger.info(f"Registered API router: {item.name}")
                    except Exception as e:
                        logger.error(f"Failed to load API {item.name}: {e}")
'''

    GRAPHQL = '''"""GraphQL schema setup"""
import strawberry
from strawberry.fastapi import GraphQLRouter
from strawberry.tools import merge_types
from pathlib import Path
import importlib
import logging

logger = logging.getLogger(__name__)

def collect_schemas():
    """Collect all GraphQL queries and mutations"""
    queries = []
    mutations = []
    
    for path_name in ['features', 'api']:
        path = Path(f"app/{path_name}")
        if not path.exists():
            continue
        
        for item in path.iterdir():
            if not item.is_dir() or item.name.startswith("_"):
                continue
            
            schema_file = item / "schema.py"
            if not schema_file.exists():
                continue
            
            try:
                module = importlib.import_module(f"app.{path_name}.{item.name}.schema")
                if hasattr(module, "Query"):
                    queries.append(module.Query)
                if hasattr(module, "Mutation"):
                    mutations.append(module.Mutation)
            except Exception as e:
                logger.error(f"Failed to load GraphQL schema from {item.name}: {e}")
    
    return queries, mutations

def setup_graphql(app):
    """Setup GraphQL endpoint"""
    queries, mutations = collect_schemas()
    
    # Default query if none found
    if not queries:
        @strawberry.type
        class Query:
            @strawberry.field
            def hello(self) -> str:
                return "Fastman GraphQL Ready"
        queries.append(Query)
    
    # Merge schemas
    ComboQuery = merge_types("Query", tuple(queries))
    ComboMutation = merge_types("Mutation", tuple(mutations)) if mutations else None
    
    schema = strawberry.Schema(
        query=ComboQuery,
        mutation=ComboMutation
    )
    
    graphql_app = GraphQLRouter(schema)
    app.include_router(graphql_app, prefix="/graphql")
    logger.info("GraphQL endpoint registered at /graphql")
'''

    ALEMBIC_ENV = '''"""Alembic environment configuration"""
from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool
from alembic import context
import sys
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parents[2]))

from app.core.config import settings
from app.core.database import Base

# Import all models here
# This ensures they're registered with Base.metadata
from app.models import *

config = context.config
config.set_main_option("sqlalchemy.url", settings.DATABASE_URL)

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata

def run_migrations_offline():
    """Run migrations in 'offline' mode"""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online():
    """Run migrations in 'online' mode"""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
'''

    ALEMBIC_INI = '''[alembic]
script_location = alembic
prepend_sys_path = .
version_path_separator = os

[loggers]
keys = root,sqlalchemy,alembic

[handlers]
keys = console

[formatters]
keys = generic

[logger_root]
level = WARN
handlers = console

[logger_sqlalchemy]
level = WARN
handlers =
qualname = sqlalchemy.engine

[logger_alembic]
level = INFO
handlers =
qualname = alembic

[handler_console]
class = StreamHandler
args = (sys.stderr,)
level = NOTSET
formatter = generic

[formatter_generic]
format = %(levelname)-5.5s [%(name)s] %(message)s
'''

    GITIGNORE = '''# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
*.egg-info/
dist/
build/
*.egg

# Virtual Environment
.venv/
venv/
ENV/
env/

# IDEs
.vscode/
.idea/
*.swp
*.swo
*~

# Environment
.env
.env.local
.env.*.local

# Database
*.db
*.sqlite
*.sqlite3

# Logs
logs/
*.log

# Testing
.pytest_cache/
.coverage
htmlcov/

# OS
.DS_Store
Thumbs.db

# Fastman
config_cache.json
'''

    ENV_TEMPLATE = '''# Application
PROJECT_NAME={project_name}
ENVIRONMENT=development
DEBUG=true
SECRET_KEY={secret_key}

# Database
DATABASE_URL=sqlite:///./app.db

# API
API_V1_PREFIX=/api/v1
ALLOWED_HOSTS=["*"]
'''


# ============================================================================
# COMMAND FRAMEWORK
# ============================================================================

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


# ============================================================================
# CORE COMMANDS
# ============================================================================

@register
class NewCommand(Command):
    signature = "new {name} {--minimal} {--pattern=feature} {--package=uv} {--database=sqlite}"
    description = "Create a new FastAPI project"
    
    def handle(self):
        name = self.validate_name(self.argument(0), "Project name is required")
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
# Database (PostgreSQL with asyncpg)
DATABASE_URL=postgresql+asyncpg://postgres:changeme@localhost:5432/{project_name}
POSTGRES_USER=postgres
POSTGRES_PASSWORD=changeme
POSTGRES_DB={project_name}
""",
            "mysql": f"""
# Database (MySQL)
DATABASE_URL=mysql+pymysql://root:changeme@localhost:3306/{project_name}
MYSQL_USER=root
MYSQL_PASSWORD=changeme
MYSQL_DATABASE={project_name}
""",
            "oracle": f"""
# Database (Oracle)
DATABASE_URL=oracle+cx_oracle://system:changeme@localhost:1521/XE
ORACLE_USER=system
ORACLE_PASSWORD=changeme
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
            base_deps.extend(["sqlalchemy", "alembic", "asyncpg"])  # Async driver for production
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


@register
class MakeFeatureCommand(Command):
    signature = "make:feature {name} {--crud}"
    description = "Create a vertical slice feature with router, service, model, and schema"
    
    def handle(self):
        name = self.validate_name(self.argument(0), "Feature name is required")
        crud = self.flag("crud")
        
        snake = NameValidator.to_snake_case(name)
        pascal = NameValidator.to_pascal_case(name)
        
        # Verify project pattern
        features_dir = Path("app/features")
        if not features_dir.exists():
            Output.error("Directory 'app/features' not found.")
            Output.info("The 'make:feature' command is only available for projects using the Feature pattern.")
            Output.info("For Layer pattern, use 'make:model', 'make:service', etc.")
            return
        
        base = features_dir / snake
        
        if base.exists():
            Output.error(f"Feature '{snake}' already exists")
            return
        
        PathManager.ensure_dir(base)
        
        # Model
        model_content = f'''"""Database model for {pascal}"""
from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.sql import func
from app.core.database import Base


class {pascal}(Base):
    """{pascal} model"""
    __tablename__ = "{snake}s"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    def __repr__(self):
        return f"<{pascal}(id={{self.id}}, name={{self.name}})>"
'''
        
        # Schemas
        schema_content = f'''"""Pydantic schemas for {pascal}"""
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional


class {pascal}Base(BaseModel):
    """Base schema with common attributes"""
    name: str = Field(..., min_length=1, max_length=255)


class {pascal}Create({pascal}Base):
    """Schema for creating a {pascal}"""
    pass


class {pascal}Update(BaseModel):
    """Schema for updating a {pascal}"""
    name: Optional[str] = Field(None, min_length=1, max_length=255)


class {pascal}Read({pascal}Base):
    """Schema for reading a {pascal}"""
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True
'''
        
        # Service
        service_content = f'''"""Business logic for {pascal}"""
from sqlalchemy.orm import Session
from typing import List, Optional
from . import models, schemas


class {pascal}Service:
    """Service layer for {pascal} operations"""
    
    @staticmethod
    def get_all(db: Session, skip: int = 0, limit: int = 100) -> List[models.{pascal}]:
        """Get all {snake}s"""
        return db.query(models.{pascal}).offset(skip).limit(limit).all()
    
    @staticmethod
    def get_by_id(db: Session, id: int) -> Optional[models.{pascal}]:
        """Get {snake} by ID"""
        return db.query(models.{pascal}).filter(models.{pascal}.id == id).first()
    
    @staticmethod
    def create(db: Session, data: schemas.{pascal}Create) -> models.{pascal}:
        """Create new {snake}"""
        obj = models.{pascal}(**data.model_dump())
        db.add(obj)
        db.commit()
        db.refresh(obj)
        return obj
    
    @staticmethod
    def update(db: Session, id: int, data: schemas.{pascal}Update) -> Optional[models.{pascal}]:
        """Update existing {snake}"""
        obj = db.query(models.{pascal}).filter(models.{pascal}.id == id).first()
        if not obj:
            return None
        
        for key, value in data.model_dump(exclude_unset=True).items():
            setattr(obj, key, value)
        
        db.commit()
        db.refresh(obj)
        return obj
    
    @staticmethod
    def delete(db: Session, id: int) -> bool:
        """Delete {snake}"""
        obj = db.query(models.{pascal}).filter(models.{pascal}.id == id).first()
        if not obj:
            return False
        
        db.delete(obj)
        db.commit()
        return True
'''
        
        # Router
        if crud:
            router_content = f'''"""API routes for {pascal}"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.core.database import get_db
from . import service, schemas


router = APIRouter(
    prefix="/{snake}s",
    tags=["{pascal}"]
)


@router.get("/", response_model=List[schemas.{pascal}Read])
async def list_{snake}s(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """Get all {snake}s"""
    return service.{pascal}Service.get_all(db, skip=skip, limit=limit)


@router.get("/{{id}}", response_model=schemas.{pascal}Read)
async def get_{snake}(id: int, db: Session = Depends(get_db)):
    """Get {snake} by ID"""
    obj = service.{pascal}Service.get_by_id(db, id)
    if not obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"{pascal} not found"
        )
    return obj


@router.post("/", response_model=schemas.{pascal}Read, status_code=status.HTTP_201_CREATED)
async def create_{snake}(
    data: schemas.{pascal}Create,
    db: Session = Depends(get_db)
):
    """Create new {snake}"""
    return service.{pascal}Service.create(db, data)


@router.put("/{{id}}", response_model=schemas.{pascal}Read)
async def update_{snake}(
    id: int,
    data: schemas.{pascal}Update,
    db: Session = Depends(get_db)
):
    """Update {snake}"""
    obj = service.{pascal}Service.update(db, id, data)
    if not obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"{pascal} not found"
        )
    return obj


@router.delete("/{{id}}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_{snake}(id: int, db: Session = Depends(get_db)):
    """Delete {snake}"""
    if not service.{pascal}Service.delete(db, id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"{pascal} not found"
        )
'''
        else:
            router_content = f'''"""API routes for {pascal}"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List
from app.core.database import get_db
from . import service, schemas


router = APIRouter(
    prefix="/{snake}s",
    tags=["{pascal}"]
)


@router.get("/", response_model=List[schemas.{pascal}Read])
async def list_{snake}s(db: Session = Depends(get_db)):
    """Get all {snake}s"""
    return service.{pascal}Service.get_all(db)
'''
        
        # Write files
        PathManager.write_file(base / "models.py", model_content)
        PathManager.write_file(base / "schemas.py", schema_content)
        PathManager.write_file(base / "service.py", service_content)
        PathManager.write_file(base / "router.py", router_content)
        
        Output.success(f"Feature '{snake}' created at app/features/{snake}/")
        Output.info("Files created:")
        Output.echo(f"  - models.py (Database model)", Style.CYAN)
        Output.echo(f"  - schemas.py (Pydantic schemas)", Style.CYAN)
        Output.echo(f"  - service.py (Business logic)", Style.CYAN)
        Output.echo(f"  - router.py ({'CRUD' if crud else 'Basic'} endpoints)", Style.CYAN)
        
        if crud:
            Output.info(f"\nGenerated CRUD endpoints:")
            Output.echo(f"  GET    /{snake}s       - List all", Style.GREEN)
            Output.echo(f"  GET    /{snake}s/{{id}}  - Get by ID", Style.GREEN)
            Output.echo(f"  POST   /{snake}s       - Create", Style.GREEN)
            Output.echo(f"  PUT    /{snake}s/{{id}}  - Update", Style.GREEN)
            Output.echo(f"  DELETE /{snake}s/{{id}}  - Delete", Style.GREEN)


@register
class MakeApiCommand(Command):
    signature = "make:api {name} {--style=rest}"
    description = "Create a lightweight API endpoint (rest or graphql)"
    
    def handle(self):
        name = self.validate_name(self.argument(0), "API name is required")
        style = self.option("style", "rest").lower()
        
        if style not in ["rest", "graphql"]:
            Output.error("Style must be 'rest' or 'graphql'")
            return
        
        snake = NameValidator.to_snake_case(name)
        pascal = NameValidator.to_pascal_case(name)
        
        base = Path("app/api") / snake
        
        if base.exists():
            Output.error(f"API '{snake}' already exists")
            return
        
        PathManager.ensure_dir(base)
        
        if style == "graphql":
            content = f'''"""GraphQL schema for {pascal}"""
import strawberry
from typing import List


@strawberry.type
class {pascal}Type:
    """GraphQL type for {pascal}"""
    id: int
    name: str


@strawberry.type
class Query:
    """GraphQL queries for {pascal}"""
    
    @strawberry.field
    def {snake}s(self) -> List[{pascal}Type]:
        """Get all {snake}s"""
        # TODO: Implement query logic
        return []
    
    @strawberry.field
    def {snake}(self, id: int) -> {pascal}Type:
        """Get {snake} by ID"""
        # TODO: Implement query logic
        return {pascal}Type(id=id, name="Example")


@strawberry.type
class Mutation:
    """GraphQL mutations for {pascal}"""
    
    @strawberry.mutation
    def create_{snake}(self, name: str) -> {pascal}Type:
        """Create a new {snake}"""
        # TODO: Implement mutation logic
        return {pascal}Type(id=1, name=name)
'''
            PathManager.write_file(base / "schema.py", content)
            Output.success(f"GraphQL API '{snake}' created at app/api/{snake}/")
            Output.info("Access at: /graphql")
        
        else:  # REST
            content = f'''"""REST API endpoints for {pascal}"""
from fastapi import APIRouter, HTTPException, status
from typing import List
from pydantic import BaseModel


router = APIRouter(
    prefix="/api/{snake}",
    tags=["{pascal} API"]
)


class {pascal}Response(BaseModel):
    """Response model"""
    id: int
    name: str


@router.get("/", response_model=List[{pascal}Response])
async def list_{snake}s():
    """List all {snake}s"""
    # TODO: Implement logic
    return []


@router.get("/{{id}}", response_model={pascal}Response)
async def get_{snake}(id: int):
    """Get {snake} by ID"""
    # TODO: Implement logic
    return {pascal}Response(id=id, name="Example")
'''
            PathManager.write_file(base / "router.py", content)
            Output.success(f"REST API '{snake}' created at app/api/{snake}/")
            Output.info(f"Endpoints:")
            Output.echo(f"  GET /api/{snake}", Style.CYAN)
            Output.echo(f"  GET /api/{snake}/{{id}}", Style.CYAN)


@register
class MakeWebSocketCommand(Command):
    signature = "make:websocket {name}"
    description = "Create WebSocket feature with connection manager"
    
    def handle(self):
        name = self.validate_name(self.argument(0), "WebSocket name is required")
        
        snake = NameValidator.to_snake_case(name)
        pascal = NameValidator.to_pascal_case(name)
        
        base = Path("app/features") / snake
        
        if base.exists():
            Output.error(f"Feature '{snake}' already exists")
            return
        
        PathManager.ensure_dir(base)
        
        # Manager
        manager_content = f'''"""WebSocket connection manager for {pascal}"""
from fastapi import WebSocket
from typing import List
import logging

logger = logging.getLogger(__name__)


class {pascal}ConnectionManager:
    """Manages WebSocket connections"""
    
    def __init__(self):
        self.active_connections: List[WebSocket] = []
    
    async def connect(self, websocket: WebSocket):
        """Accept and register new connection"""
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"New connection. Total: {{len(self.active_connections)}}")
    
    def disconnect(self, websocket: WebSocket):
        """Remove connection"""
        self.active_connections.remove(websocket)
        logger.info(f"Connection closed. Total: {{len(self.active_connections)}}")
    
    async def send_personal(self, message: str, websocket: WebSocket):
        """Send message to specific connection"""
        await websocket.send_text(message)
    
    async def broadcast(self, message: str):
        """Broadcast message to all connections"""
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except Exception as e:
                logger.error(f"Failed to send message: {{e}}")


# Singleton instance
manager = {pascal}ConnectionManager()
'''
        
        # Router
        router_content = f'''"""WebSocket routes for {pascal}"""
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from .manager import manager
import logging

logger = logging.getLogger(__name__)

router = APIRouter(tags=["{pascal} WebSocket"])


@router.websocket("/ws/{snake}")
async def {snake}_endpoint(websocket: WebSocket):
    """WebSocket endpoint for {snake}"""
    await manager.connect(websocket)
    
    try:
        while True:
            # Receive message from client
            data = await websocket.receive_text()
            
            logger.info(f"Received: {{data}}")
            
            # Echo back to sender
            await manager.send_personal(f"Echo: {{data}}", websocket)
            
            # Broadcast to all
            await manager.broadcast(f"Broadcast: {{data}}")
    
    except WebSocketDisconnect:
        manager.disconnect(websocket)
        await manager.broadcast(f"Client disconnected")
    except Exception as e:
        logger.error(f"WebSocket error: {{e}}")
        manager.disconnect(websocket)
'''
        
        PathManager.write_file(base / "manager.py", manager_content)
        PathManager.write_file(base / "router.py", router_content)
        
        Output.success(f"WebSocket feature '{snake}' created")
        Output.info(f"Connect to: ws://localhost:8000/ws/{snake}")


@register
class MakeControllerCommand(Command):
    signature = "make:controller {name}"
    description = "Create a controller class"
    
    def handle(self):
        name = self.validate_name(self.argument(0), "Controller name is required")
        
        snake = NameValidator.to_snake_case(name)
        pascal = NameValidator.to_pascal_case(name)
        
        # Determine path
        path = self.context.project_root / "app" / "http" / "controllers" / f"{snake}.py"
        PathManager.ensure_dir(path.parent)
        
        content = f'''"""
{pascal} Controller
"""
from fastapi import Request

class {pascal}Controller:
    """
    Controller for {name}
    """
    
    def index(self, request: Request):
        return {{"message": "Hello from {pascal}Controller"}}
'''
        
        if PathManager.write_file(path, content):
            Output.success(f"Controller created: {path.relative_to(self.context.project_root)}")

@register
class MakeModelCommand(Command):
    signature = "make:model {name} {--table=}"
    description = "Create database model"
    
    def handle(self):
        name = self.validate_name(self.argument(0), "Model name is required")
        table = self.option("table")
        
        snake = NameValidator.to_snake_case(name)
        pascal = NameValidator.to_pascal_case(name)
        table_name = table or f"{snake}s"
        
        path = Path("app/models") / f"{snake}.py"
        
        if path.exists():
            Output.error(f"Model '{snake}' already exists")
            return
        
        content = f'''"""Database model for {pascal}"""
from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text
from sqlalchemy.sql import func
from app.core.database import Base


class {pascal}(Base):
    """{pascal} model"""
    __tablename__ = "{table_name}"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    def __repr__(self):
        return f"<{pascal}(id={{self.id}}, name={{self.name}})>"
'''
        
        PathManager.write_file(path, content)
        Output.success(f"Model '{pascal}' created at {path}")
        
        # Auto-register in __init__.py
        init_path = Path("app/models/__init__.py")
        import_line = f"from .{snake} import {pascal}"
        
        if init_path.exists():
            current_content = init_path.read_text(encoding='utf-8')
            if import_line not in current_content:
                # Append to end of file
                if current_content and not current_content.endswith('\n'):
                    current_content += '\n'
                current_content += f"{import_line}\n"
                PathManager.write_file(init_path, current_content, overwrite=True)
                Output.success(f"Registered in app/models/__init__.py")
        else:
            # Create new file
            PathManager.write_file(init_path, f"{import_line}\n")
            Output.success(f"Created app/models/__init__.py with registration")


@register
class MakeServiceCommand(Command):
    signature = "make:service {name}"
    description = "Create service class for business logic"
    
    def handle(self):
        name = self.validate_name(self.argument(0), "Service name is required")
        
        snake = NameValidator.to_snake_case(name)
        pascal = NameValidator.to_pascal_case(name)
        
        path = Path("app/services") / f"{snake}.py"
        
        if path.exists():
            Output.error(f"Service '{snake}' already exists")
            return
        
        content = f'''"""Business logic service for {pascal}"""
from typing import Any, Dict
import logging

logger = logging.getLogger(__name__)


class {pascal}Service:
    """{pascal} service layer"""
    
    def __init__(self):
        """Initialize service"""
        pass
    
    def execute(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Main service method
        
        Args:
            data: Input data
            
        Returns:
            Result dictionary
        """
        logger.info(f"{pascal}Service.execute called")
        
        # TODO: Implement business logic
        
        return {{"status": "success", "data": data}}
    
    def validate(self, data: Dict[str, Any]) -> bool:
        """
        Validate input data
        
        Args:
            data: Data to validate
            
        Returns:
            True if valid
        """
        # TODO: Implement validation
        return True
'''
        
        PathManager.write_file(path, content)
        Output.success(f"Service '{pascal}' created at {path}")


@register
class MakeMiddlewareCommand(Command):
    signature = "make:middleware {name}"
    description = "Create HTTP middleware"
    
    def handle(self):
        name = self.validate_name(self.argument(0), "Middleware name is required")
        
        snake = NameValidator.to_snake_case(name)
        pascal = NameValidator.to_pascal_case(name)
        
        path = Path("app/middleware") / f"{snake}.py"
        
        if path.exists():
            Output.error(f"Middleware '{snake}' already exists")
            return
        
        content = f'''"""HTTP middleware for {pascal}"""
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
import logging
import time

logger = logging.getLogger(__name__)


class {pascal}Middleware(BaseHTTPMiddleware):
    """{pascal} middleware"""
    
    async def dispatch(self, request: Request, call_next) -> Response:
        """
        Process request
        
        Args:
            request: Incoming request
            call_next: Next middleware/route handler
            
        Returns:
            Response
        """
        # Before request
        start_time = time.time()
        logger.info(f"{{request.method}} {{request.url.path}}")
        
        # Process request
        response = await call_next(request)
        
        # After request
        process_time = time.time() - start_time
        response.headers["X-Process-Time"] = str(process_time)
        logger.info(f"Completed in {{process_time:.4f}}s")
        
        return response
'''
        
        PathManager.write_file(path, content)
        Output.success(f"Middleware '{pascal}' created at {path}")
        Output.info("Add to app/main.py:")
        Output.echo(f"  from app.middleware.{snake} import {pascal}Middleware", Style.CYAN)
        Output.echo(f"  app.add_middleware({pascal}Middleware)", Style.CYAN)


@register
class MakeDependencyCommand(Command):
    signature = "make:dependency {name}"
    description = "Create FastAPI dependency"
    
    def handle(self):
        name = self.validate_name(self.argument(0), "Dependency name is required")
        
        snake = NameValidator.to_snake_case(name)
        pascal = NameValidator.to_pascal_case(name)
        
        path = Path("app/dependencies") / f"{snake}.py"
        
        if path.exists():
            Output.error(f"Dependency '{snake}' already exists")
            return
        
        content = f'''"""FastAPI dependency for {pascal}"""
from fastapi import Depends, HTTPException, status
from typing import Optional
import logging

logger = logging.getLogger(__name__)


async def get_{snake}() -> str:
    """
    Dependency function for {pascal}
    
    Returns:
        Dependency value
        
    Raises:
        HTTPException: If dependency cannot be resolved
    """
    try:
        # TODO: Implement dependency logic
        logger.info("Resolving {snake} dependency")
        return "{snake}_value"
    except Exception as e:
        logger.error(f"Failed to resolve {snake}: {{e}}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to resolve dependency"
        )


class {pascal}Dependency:
    """Class-based dependency for {pascal}"""
    
    def __init__(self, param: Optional[str] = None):
        self.param = param
    
    async def __call__(self) -> str:
        """Execute dependency"""
        logger.info(f"{pascal}Dependency called with param={{self.param}}")
        # TODO: Implement logic
        return "result"
'''
        
        PathManager.write_file(path, content)
        Output.success(f"Dependency '{pascal}' created at {path}")
        Output.info("Use in routes:")
        Output.echo(f"  from app.dependencies.{snake} import get_{snake}", Style.CYAN)
        Output.echo(f"  async def route(dep = Depends(get_{snake})):", Style.CYAN)


@register
class MakeTestCommand(Command):
    signature = "make:test {name}"
    description = "Create test file"
    
    def handle(self):
        name = self.validate_name(self.argument(0), "Test name is required")
        
        snake = NameValidator.to_snake_case(name)
        pascal = NameValidator.to_pascal_case(name)
        
        path = Path("tests") / f"test_{snake}.py"
        
        if path.exists():
            Output.error(f"Test '{snake}' already exists")
            return
        
        content = f'''"""Tests for {pascal}"""
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


class Test{pascal}:
    """Test suite for {pascal}"""
    
    def test_example(self):
        """Example test"""
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "ok"
    
    @pytest.mark.asyncio
    async def test_async_example(self):
        """Example async test"""
        # TODO: Implement test
        assert True
    
    def test_create(self):
        """Test creation"""
        # TODO: Implement test
        pass
    
    def test_read(self):
        """Test reading"""
        # TODO: Implement test
        pass
    
    def test_update(self):
        """Test updating"""
        # TODO: Implement test
        pass
    
    def test_delete(self):
        """Test deletion"""
        # TODO: Implement test
        pass
'''
        
        PathManager.write_file(path, content)
        Output.success(f"Test '{pascal}' created at {path}")
        Output.info("Run with: pytest tests/")


# ============================================================================
# DATABASE COMMANDS
# ============================================================================

@register
class MakeMigrationCommand(Command):
    signature = "make:migration {message}"
    description = "Create database migration"
    
    def handle(self):
        message = self.argument(0, "update")
        
        # Sanitize message
        message = re.sub(r'[^\w\s-]', '', message).strip()
        
        cmd = PackageManager.get_run_prefix() + [
            "alembic", "revision", "--autogenerate", "-m", message
        ]
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode == 0:
                Output.success(f"Migration created: {message}")
                Output.info("Review the migration file before running migrate")
            else:
                Output.error(f"Migration failed: {result.stderr}")
        except Exception as e:
            Output.error(f"Failed to create migration: {e}")


@register
class MigrateCommand(Command):
    signature = "migrate"
    description = "Run database migrations"
    
    def handle(self):
        cmd = PackageManager.get_run_prefix() + ["alembic", "upgrade", "head"]
        
        Output.info("Running migrations...")
        try:
            result = subprocess.run(cmd)
            if result.returncode == 0:
                Output.success("Migrations completed")
            else:
                Output.error("Migration failed")
        except Exception as e:
            Output.error(f"Failed to run migrations: {e}")


@register
class MigrateRollbackCommand(Command):
    signature = "migrate:rollback {--steps=1}"
    description = "Rollback database migrations"
    
    def handle(self):
        steps = self.option("steps", "1")
        
        if not Output.confirm(f"Rollback {steps} migration(s)?", default=False):
            Output.info("Cancelled")
            return
        
        cmd = PackageManager.get_run_prefix() + ["alembic", "downgrade", f"-{steps}"]
        
        try:
            result = subprocess.run(cmd)
            if result.returncode == 0:
                Output.success(f"Rolled back {steps} migration(s)")
            else:
                Output.error("Rollback failed")
        except Exception as e:
            Output.error(f"Failed to rollback: {e}")


@register
class MigrateResetCommand(Command):
    signature = "migrate:reset"
    description = "Reset database (rollback all migrations)"
    
    def handle(self):
        if not Output.confirm("⚠️  Reset ALL migrations? This cannot be undone!", default=False):
            Output.info("Cancelled")
            return
        
        cmd = PackageManager.get_run_prefix() + ["alembic", "downgrade", "base"]
        
        try:
            result = subprocess.run(cmd)
            if result.returncode == 0:
                Output.success("Database reset complete")
            else:
                Output.error("Reset failed")
        except Exception as e:
            Output.error(f"Failed to reset: {e}")


@register
class MigrateStatusCommand(Command):
    signature = "migrate:status"
    description = "Show migration status"
    
    def handle(self):
        cmd = PackageManager.get_run_prefix() + ["alembic", "current"]
        
        try:
            subprocess.run(cmd)
        except Exception as e:
            Output.error(f"Failed to get status: {e}")


# ============================================================================
# UTILITY COMMANDS
# ============================================================================

@register
class RouteListCommand(Command):
    signature = "route:list {--path=} {--method=}"
    description = "List all API routes"
    
    def handle(self):
        path_filter = self.option("path")
        method_filter = self.option("method", "").upper()
        
        sys.path.insert(0, str(Path.cwd()))
        
        try:
            from app.main import app
            
            routes = []
            for route in app.routes:
                route_path = getattr(route, "path", "")
                route_methods = getattr(route, "methods", set())
                
                # Apply filters
                if path_filter and path_filter not in route_path:
                    continue
                if method_filter and method_filter not in route_methods:
                    continue
                
                methods_str = ",".join(sorted(route_methods)) if route_methods else "WS"
                name = getattr(route, "name", "-")
                
                routes.append([methods_str, route_path, name])
            
            if routes:
                Output.table(
                    ["Methods", "Path", "Name"],
                    routes,
                    "API Routes"
                )
                Output.info(f"Total routes: {len(routes)}")
            else:
                Output.warn("No routes found")
        
        except Exception as e:
            Output.error(f"Failed to load routes: {e}")
            logger.exception(e)


@register
class TinkerCommand(Command):
    signature = "tinker"
    description = "Interactive Python shell with app context"
    
    def handle(self):
        sys.path.insert(0, str(Path.cwd()))
        
        # Import commonly used items
        namespace = {}
        try:
            from app.core.config import settings
            from app.core.database import SessionLocal, Base
            namespace.update({
                "settings": settings,
                "SessionLocal": SessionLocal,
                "Base": Base,
                "db": SessionLocal()
            })
        except:
            pass
        
        Output.info("Fastman Interactive Shell")
        Output.info("Available: settings, SessionLocal, Base, db")
        
        try:
            import IPython
            IPython.start_ipython(argv=[], user_ns=namespace)
        except ImportError:
            import code
            code.interact(local=namespace)


@register
class GenerateKeyCommand(Command):
    signature = "generate:key {--show}"
    description = "Generate secret key"
    
    def handle(self):
        key = secrets.token_urlsafe(32)
        show_only = self.flag("show")
        
        if show_only:
            Output.success(f"Generated key: {key}")
            return
        
        env_file = Path(".env")
        
        if env_file.exists():
            content = env_file.read_text()
            
            if "SECRET_KEY=" in content:
                # Update existing key
                content = re.sub(
                    r'SECRET_KEY=.*',
                    f'SECRET_KEY={key}',
                    content
                )
            else:
                # Add new key
                content += f"\nSECRET_KEY={key}\n"
            
            env_file.write_text(content)
            Output.success("Secret key updated in .env")
        else:
            # Create new .env
            env_file.write_text(f"SECRET_KEY={key}\n")
            Output.success("Secret key created in .env")
        
        Output.info(f"Key: {key}")


@register
class ConfigCacheCommand(Command):
    signature = "config:cache"
    description = "Cache environment configuration"
    
    def handle(self):
        env_file = Path(".env")
        
        if not env_file.exists():
            Output.error(".env file not found")
            return
        
        config = {}
        for line in env_file.read_text().splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, value = line.split("=", 1)
                config[key.strip()] = value.strip()
        
        cache_file = Path("config_cache.json")
        cache_file.write_text(json.dumps(config, indent=2))
        
        Output.success(f"Configuration cached ({len(config)} variables)")


@register
class ConfigClearCommand(Command):
    signature = "config:clear"
    description = "Clear configuration cache"
    
    def handle(self):
        cache_file = Path("config_cache.json")
        
        if cache_file.exists():
            cache_file.unlink()
            Output.success("Configuration cache cleared")
        else:
            Output.info("No cache to clear")


@register
class CacheClearCommand(Command):
    signature = "cache:clear"
    description = "Clear Python cache files"
    
    def handle(self):
        count = 0
        
        for root, dirs, files in os.walk("."):
            # Remove __pycache__ directories
            for dir_name in dirs:
                if dir_name == "__pycache__":
                    dir_path = Path(root) / dir_name
                    shutil.rmtree(dir_path)
                    count += 1
            
            # Remove .pyc files
            for file_name in files:
                if file_name.endswith(".pyc"):
                    file_path = Path(root) / file_name
                    file_path.unlink()
                    count += 1
        
        Output.success(f"Cleared {count} cache files/directories")


@register
class InstallAuthCommand(Command):
    signature = "install:auth {--type=jwt} {--provider=}"
    description = "Install authentication scaffolding (jwt, oauth, keycloak)"
    
    def handle(self):
        auth_type = self.option("type", "jwt").lower()
        provider = self.option("provider")
        
        if auth_type == "jwt":
            self._install_jwt()
        elif auth_type == "oauth":
            self._install_oauth(provider)
        elif auth_type == "keycloak":
            self._install_keycloak()
        else:
            Output.error(f"Unknown auth type: {auth_type}")
            Output.info("Available types: jwt, oauth, keycloak")
    
    def _install_jwt(self):
        """Install JWT authentication"""
        Output.info("Installing JWT authentication...")
        
        # Install dependencies
        packages = [
            "pyjwt",
            "passlib[bcrypt]",
            "python-multipart"
        ]
        
        if not PackageManager.install(packages):
            Output.error("Failed to install dependencies")
            return
        
        # Create auth feature
        base = Path("app/features/auth")
        PathManager.ensure_dir(base)
        
        # Security utilities
        security_content = '''"""JWT security utilities"""
from datetime import datetime, timedelta, timezone
from typing import Optional
import jwt
from passlib.context import CryptContext
from app.core.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password against hash"""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Hash password"""
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create JWT access token"""
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=ALGORITHM)
    
    return encoded_jwt


def decode_token(token: str) -> Optional[dict]:
    """Decode and verify JWT token"""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.InvalidTokenError:
        return None
'''
        
        # Auth models
        models_content = '''"""Authentication models"""
from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sqlalchemy.sql import func
from app.core.database import Base


class User(Base):
    """User model"""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    username = Column(String(100), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    def __repr__(self):
        return f"<User(id={self.id}, email={self.email})>"
'''
        
        # Auth schemas
        schemas_content = '''"""Authentication schemas"""
from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime


class UserBase(BaseModel):
    """Base user schema"""
    email: EmailStr
    username: str = Field(..., min_length=3, max_length=100)


class UserCreate(UserBase):
    """Schema for user registration"""
    password: str = Field(..., min_length=8)


class UserUpdate(BaseModel):
    """Schema for user update"""
    email: Optional[EmailStr] = None
    username: Optional[str] = Field(None, min_length=3, max_length=100)
    password: Optional[str] = Field(None, min_length=8)


class UserRead(UserBase):
    """Schema for user response"""
    id: int
    is_active: bool
    is_superuser: bool
    created_at: datetime
    
    class Config:
        from_attributes = True


class Token(BaseModel):
    """Token response schema"""
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    """Token payload schema"""
    username: Optional[str] = None
'''
        
        # Auth service
        service_content = '''"""Authentication service"""
from sqlalchemy.orm import Session
from typing import Optional
from . import models, schemas
from .security import get_password_hash, verify_password


class AuthService:
    """Authentication service layer"""
    
    @staticmethod
    def get_user_by_email(db: Session, email: str) -> Optional[models.User]:
        """Get user by email"""
        return db.query(models.User).filter(models.User.email == email).first()
    
    @staticmethod
    def get_user_by_username(db: Session, username: str) -> Optional[models.User]:
        """Get user by username"""
        return db.query(models.User).filter(models.User.username == username).first()
    
    @staticmethod
    def create_user(db: Session, user_data: schemas.UserCreate) -> models.User:
        """Create new user"""
        hashed_password = get_password_hash(user_data.password)
        
        user = models.User(
            email=user_data.email,
            username=user_data.username,
            hashed_password=hashed_password
        )
        
        db.add(user)
        db.commit()
        db.refresh(user)
        
        return user
    
    @staticmethod
    def authenticate_user(db: Session, username: str, password: str) -> Optional[models.User]:
        """Authenticate user"""
        user = AuthService.get_user_by_username(db, username)
        
        if not user:
            return None
        
        if not verify_password(password, user.hashed_password):
            return None
        
        return user
'''
        
        # Auth dependencies
        dependencies_content = '''"""Authentication dependencies"""
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from app.core.database import get_db
from . import models, service
from .security import decode_token

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> models.User:
    """Get current authenticated user"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    payload = decode_token(token)
    if payload is None:
        raise credentials_exception
    
    username: str = payload.get("sub")
    if username is None:
        raise credentials_exception
    
    user = service.AuthService.get_user_by_username(db, username)
    if user is None:
        raise credentials_exception
    
    return user


async def get_current_active_user(
    current_user: models.User = Depends(get_current_user)
) -> models.User:
    """Get current active user"""
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user
'''
        
        # Auth router
        router_content = '''"""Authentication routes"""
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import timedelta
from app.core.database import get_db
from . import schemas, service
from .security import create_access_token, ACCESS_TOKEN_EXPIRE_MINUTES
from .dependencies import get_current_active_user

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=schemas.UserRead, status_code=status.HTTP_201_CREATED)
async def register(user_data: schemas.UserCreate, db: Session = Depends(get_db)):
    """Register new user"""
    # Check if user exists
    if service.AuthService.get_user_by_email(db, user_data.email):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    if service.AuthService.get_user_by_username(db, user_data.username):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already taken"
        )
    
    user = service.AuthService.create_user(db, user_data)
    return user


@router.post("/login", response_model=schemas.Token)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """Login user"""
    user = service.AuthService.authenticate_user(db, form_data.username, form_data.password)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username},
        expires_delta=access_token_expires
    )
    
    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/me", response_model=schemas.UserRead)
async def get_me(current_user: schemas.UserRead = Depends(get_current_active_user)):
    """Get current user info"""
    return current_user
'''
        
        # Write files
        PathManager.write_file(base / "security.py", security_content)
        PathManager.write_file(base / "models.py", models_content)
        PathManager.write_file(base / "schemas.py", schemas_content)
        PathManager.write_file(base / "service.py", service_content)
        PathManager.write_file(base / "dependencies.py", dependencies_content)
        PathManager.write_file(base / "router.py", router_content)
        
        Output.success("JWT authentication installed!")
        Output.info("\nEndpoints created:")
        Output.echo("  POST /auth/register - Register new user", Style.GREEN)
        Output.echo("  POST /auth/login - Login user", Style.GREEN)
        Output.echo("  GET  /auth/me - Get current user", Style.GREEN)
        Output.info("\nNext steps:")
        Output.echo("  1. Run: fastman make:migration 'add users table'", Style.CYAN)
        Output.echo("  2. Run: fastman migrate", Style.CYAN)
        Output.echo("  3. Test at: http://localhost:8000/docs", Style.CYAN)
    
    def _install_oauth(self, provider: Optional[str]):
        """Install OAuth authentication"""
        Output.info(f"Installing OAuth authentication ({provider or 'generic'})...")
        
        packages = ["authlib", "httpx"]
        if not PackageManager.install(packages):
            Output.error("Failed to install dependencies")
            return
        
        Output.success("OAuth packages installed")
        Output.info("Manual configuration required - see: https://docs.authlib.org/")
    
    def _install_keycloak(self):
        """Install Keycloak authentication"""
        Output.info("Installing Keycloak authentication...")
        
        packages = ["fastapi-keycloak-middleware"]
        if not PackageManager.install(packages):
            Output.error("Failed to install dependencies")
            return
        
        # Create keycloak configuration file
        keycloak_config = '''"""Keycloak authentication configuration"""
from fastapi import FastAPI
from fastapi_keycloak_middleware import KeycloakConfiguration, setup_keycloak_middleware
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

# Keycloak configuration
keycloak_config = KeycloakConfiguration(
    url=settings.KEYCLOAK_URL,
    realm=settings.KEYCLOAK_REALM,
    client_id=settings.KEYCLOAK_CLIENT_ID,
    client_secret=settings.KEYCLOAK_CLIENT_SECRET,
    admin_client_secret=settings.KEYCLOAK_ADMIN_SECRET if hasattr(settings, 'KEYCLOAK_ADMIN_SECRET') else None
)

def init_keycloak(app: FastAPI):
    """Initialize Keycloak middleware"""
    try:
        setup_keycloak_middleware(app, keycloak_config)
        logger.info("Keycloak middleware initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize Keycloak: {e}")
        raise
'''
        
        # Write keycloak.py
        keycloak_path = Path("app/core/keycloak.py")
        PathManager.write_file(keycloak_path, keycloak_config)
        
        # Update config.py to include Keycloak settings
        config_path = Path("app/core/config.py")
        if config_path.exists():
            config_content = config_path.read_text(encoding='utf-8')
            
            # Check if Keycloak settings already exist
            if "KEYCLOAK_URL" not in config_content:
                # Add Keycloak settings before the Config class
                keycloak_settings = '''
    # Keycloak
    KEYCLOAK_URL: str = "http://localhost:8080"
    KEYCLOAK_REALM: str = "master"
    KEYCLOAK_CLIENT_ID: str = ""
    KEYCLOAK_CLIENT_SECRET: str = ""
    KEYCLOAK_ADMIN_SECRET: Optional[str] = None
    '''
                
                # Insert before "class Config:"
                config_content = config_content.replace(
                    "    # API",
                    keycloak_settings + "\n    # API"
                )
                
                config_path.write_text(config_content, encoding='utf-8')
                Output.info("Updated config.py with Keycloak settings")
        
        # Update main.py to initialize Keycloak
        main_path = Path("app/main.py")
        if main_path.exists():
            main_content = main_path.read_text(encoding='utf-8')
            
            # Check if Keycloak is already imported
            if "from app.core.keycloak import init_keycloak" not in main_content:
                # Add import after other core imports
                main_content = main_content.replace(
                    "from app.core.logging import setup_logging",
                    "from app.core.logging import setup_logging\nfrom app.core.keycloak import init_keycloak"
                )
                
                # Add initialization after CORS middleware
                main_content = main_content.replace(
                    "    allow_headers=[\"*\"],\n)",
                    "    allow_headers=[\"*\"],\n)\n\n# Initialize Keycloak\ninit_keycloak(app)"
                )
                
                main_path.write_text(main_content, encoding='utf-8')
                Output.info("Updated main.py with Keycloak initialization")
        
        # Update .env file
        env_path = Path(".env")
        if env_path.exists():
            env_content = env_path.read_text(encoding='utf-8')
            
            if "KEYCLOAK_URL" not in env_content:
                keycloak_env = '''
# Keycloak Authentication
KEYCLOAK_URL=http://localhost:8080
KEYCLOAK_REALM=master
KEYCLOAK_CLIENT_ID=your-client-id
KEYCLOAK_CLIENT_SECRET=your-client-secret
'''
                env_content += keycloak_env
                env_path.write_text(env_content, encoding='utf-8')
                Output.info("Updated .env with Keycloak configuration")
        
        Output.success("Keycloak authentication installed!")
        Output.info("\nFiles created/updated:")
        Output.echo("  app/core/keycloak.py - Keycloak configuration", Style.GREEN)
        Output.echo("  app/core/config.py - Added Keycloak settings", Style.GREEN)
        Output.echo("  app/main.py - Added Keycloak initialization", Style.GREEN)
        Output.echo("  .env - Added Keycloak environment variables", Style.GREEN)
        Output.info("\nNext steps:")
        Output.echo("  1. Update .env with your Keycloak credentials", Style.CYAN)
        Output.echo("  2. Restart your server", Style.CYAN)
        Output.echo("  3. All routes are now protected by Keycloak", Style.CYAN)
        Output.info("\nTo access user info in routes:")
        Output.echo("  request.state.user - Contains Keycloak user info", Style.YELLOW)


@register
class ImportCommand(Command):
    signature = "import {package}"
    description = "Install Python package"
    
    def handle(self):
        package = self.argument(0)
        
        if not package:
            Output.error("Package name required")
            return
        
        Output.info(f"Installing {package}...")
        
        if PackageManager.install([package]):
            Output.success(f"Package '{package}' installed")
        else:
            Output.error(f"Failed to install '{package}'")


@register
class PkgListCommand(Command):
    signature = "pkg:list"
    description = "List installed packages"
    
    def handle(self):
        manager, _ = PackageManager.detect()
        
        Output.info(f"Using package manager: {manager}")
        
        if manager == "uv":
            subprocess.run(["uv", "pip", "list"])
        elif manager == "poetry":
            subprocess.run(["poetry", "show"])
        elif manager == "pipenv":
            subprocess.run(["pipenv", "list"])
        else:
            subprocess.run([sys.executable, "-m", "pip", "list"])


@register
class MakeSeederCommand(Command):
    signature = "make:seeder {name}"
    description = "Create database seeder"
    
    def handle(self):
        name = self.validate_name(self.argument(0), "Seeder name is required")
        
        snake = NameValidator.to_snake_case(name)
        pascal = NameValidator.to_pascal_case(name)
        
        path = Path("database/seeders") / f"{snake}_seeder.py"
        
        if path.exists():
            Output.error(f"Seeder '{snake}' already exists")
            return
        
        content = f'''"""Database seeder for {pascal}"""
from sqlalchemy.orm import Session
from faker import Faker
import logging

logger = logging.getLogger(__name__)
fake = Faker()


class {pascal}Seeder:
    """Seeder for {pascal} data"""
    
    @staticmethod
    def run(db: Session):
        """
        Run the seeder
        
        Args:
            db: Database session
        """
        logger.info("Running {pascal}Seeder...")
        
        # TODO: Implement seeding logic
        # Example:
        # from app.models.{snake} import {pascal}
        # 
        # for _ in range(10):
        #     obj = {pascal}(
        #         name=fake.name(),
        #         email=fake.email()
        #     )
        #     db.add(obj)
        # 
        # db.commit()
        
        logger.info("{pascal}Seeder completed")
'''
        
        PathManager.write_file(path, content)
        Output.success(f"Seeder '{pascal}' created at {path}")
        
        # Ensure faker is installed
        try:
            import faker
        except ImportError:
            Output.info("Installing faker for seeding...")
            PackageManager.install(["faker"])


@register
class DbSeedCommand(Command):
    signature = "db:seed {--class=}"
    description = "Run database seeders"
    
    def handle(self):
        seeder_class = self.option("class")
        
        sys.path.insert(0, str(Path.cwd()))
        
        try:
            from app.core.database import SessionLocal
            
            db = SessionLocal()
            
            seeders_path = Path("database/seeders")
            if not seeders_path.exists():
                Output.error("Seeders directory not found")
                return
            
            count = 0
            for file_path in seeders_path.glob("*_seeder.py"):
                module_name = file_path.stem
                
                if seeder_class and module_name != seeder_class:
                    continue
                
                try:
                    module = importlib.import_module(f"database.seeders.{module_name}")
                    
                    # Find seeder class
                    for attr_name in dir(module):
                        if attr_name.endswith("Seeder") and attr_name != "Seeder":
                            seeder_cls = getattr(module, attr_name)
                            Output.info(f"Running {attr_name}...")
                            seeder_cls.run(db)
                            count += 1
                
                except Exception as e:
                    Output.error(f"Failed to run {module_name}: {e}")
                    logger.exception(e)
            
            db.close()
            
            if count > 0:
                Output.success(f"Ran {count} seeder(s)")
            else:
                Output.warn("No seeders found")
        
        except Exception as e:
            Output.error(f"Seeding failed: {e}")
            logger.exception(e)


@register
class MakeFactoryCommand(Command):
    signature = "make:factory {name}"
    description = "Create model factory for testing"
    
    def handle(self):
        name = self.validate_name(self.argument(0), "Factory name is required")
        
        snake = NameValidator.to_snake_case(name)
        pascal = NameValidator.to_pascal_case(name)
        
        path = Path("database/factories") / f"{snake}_factory.py"
        
        if path.exists():
            Output.error(f"Factory '{snake}' already exists")
            return
        
        content = f'''"""Factory for {pascal} model"""
from faker import Faker
from typing import Dict, Any

fake = Faker()


def {pascal}Factory(**overrides: Any) -> Dict[str, Any]:
    """
    Factory for creating {pascal} test data
    
    Args:
        **overrides: Override default values
        
    Returns:
        Dictionary with model data
    """
    data = {{
        "name": fake.name(),
        "email": fake.email(),
        "is_active": True,
        # Add more fields as needed
    }}
    
    data.update(overrides)
    return data


def create_{snake}(db, **overrides):
    """
    Create and persist {pascal} instance
    
    Args:
        db: Database session
        **overrides: Override default values
        
    Returns:
        Created model instance
    """
    from app.models.{snake} import {pascal}
    
    data = {pascal}Factory(**overrides)
    obj = {pascal}(**data)
    
    db.add(obj)
    db.commit()
    db.refresh(obj)
    
    return obj
'''
        
        PathManager.write_file(path, content)
        Output.success(f"Factory '{pascal}' created at {path}")
        Output.info("Use in tests:")
        Output.echo(f"  from database.factories.{snake}_factory import create_{snake}", Style.CYAN)
        Output.echo(f"  obj = create_{snake}(db, name='Custom')", Style.CYAN)


@register
class MakeExceptionCommand(Command):
    signature = "make:exception {name}"
    description = "Create custom exception class"
    
    def handle(self):
        name = self.validate_name(self.argument(0), "Exception name is required")
        
        snake = NameValidator.to_snake_case(name)
        pascal = NameValidator.to_pascal_case(name)
        
        # Ensure name ends with Exception
        if not pascal.endswith("Exception"):
            pascal += "Exception"
        
        path = Path("app/core/exceptions") / f"{snake}.py"
        
        if path.exists():
            Output.error(f"Exception '{pascal}' already exists")
            return
        
        content = f'''"""Custom exception: {pascal}"""
from fastapi import HTTPException, status


class {pascal}(HTTPException):
    """Custom exception for {snake} errors"""
    
    def __init__(self, detail: str = "An error occurred", status_code: int = status.HTTP_400_BAD_REQUEST):
        super().__init__(status_code=status_code, detail=detail)


class {pascal}NotFound(HTTPException):
    """Resource not found exception"""
    
    def __init__(self, detail: str = "Resource not found"):
        super().__init__(status_code=status.HTTP_404_NOT_FOUND, detail=detail)


class {pascal}Forbidden(HTTPException):
    """Forbidden access exception"""
    
    def __init__(self, detail: str = "Forbidden"):
        super().__init__(status_code=status.HTTP_403_FORBIDDEN, detail=detail)
'''
        
        PathManager.write_file(path, content)
        Output.success(f"Exception '{pascal}' created at {path}")


@register
class MakeRepositoryCommand(Command):
    signature = "make:repository {name}"
    description = "Create repository pattern class"
    
    def handle(self):
        name = self.validate_name(self.argument(0), "Repository name is required")
        
        snake = NameValidator.to_snake_case(name)
        pascal = NameValidator.to_pascal_case(name)
        
        path = Path("app/repositories") / f"{snake}_repository.py"
        
        if path.exists():
            Output.error(f"Repository '{snake}' already exists")
            return
        
        content = f'''"""Repository for {pascal} data access"""
from sqlalchemy.orm import Session
from typing import List, Optional, Any, Dict
from app.models.{snake} import {pascal}


class {pascal}Repository:
    """Data access layer for {pascal}"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_all(self, skip: int = 0, limit: int = 100) -> List[{pascal}]:
        """Get all records"""
        return self.db.query({pascal}).offset(skip).limit(limit).all()
    
    def get_by_id(self, id: int) -> Optional[{pascal}]:
        """Get record by ID"""
        return self.db.query({pascal}).filter({pascal}.id == id).first()
    
    def create(self, data: Dict[str, Any]) -> {pascal}:
        """Create new record"""
        obj = {pascal}(**data)
        self.db.add(obj)
        self.db.commit()
        self.db.refresh(obj)
        return obj
    
    def update(self, id: int, data: Dict[str, Any]) -> Optional[{pascal}]:
        """Update existing record"""
        obj = self.get_by_id(id)
        
        if not obj:
            return None
        
        for key, value in data.items():
            setattr(obj, key, value)
        
        self.db.commit()
        self.db.refresh(obj)
        return obj
    
    def delete(self, id: int) -> bool:
        """Delete record"""
        obj = self.get_by_id(id)
        
        if not obj:
            return False
        
        self.db.delete(obj)
        self.db.commit()
        return True
    
    def find_by(self, **filters) -> List[{pascal}]:
        """Find records by filters"""
        query = self.db.query({pascal})
        
        for key, value in filters.items():
            if hasattr({pascal}, key):
                query = query.filter(getattr({pascal}, key) == value)
        
        return query.all()
'''
        
        PathManager.write_file(path, content)
        Output.success(f"Repository '{pascal}' created at {path}")


@register
class MakeCommandCommand(Command):
    signature = "make:command {name}"
    description = "Create custom CLI command"
    
    def handle(self):
        name = self.validate_name(self.argument(0), "Command name is required")
        
        snake = NameValidator.to_snake_case(name)
        pascal = NameValidator.to_pascal_case(name)
        
        path = Path("app/console/commands") / f"{snake}.py"
        
        if path.exists():
            Output.error(f"Command '{snake}' already exists")
            return
        
        content = f'''"""Custom command: {pascal}"""
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parents[3]))

from fastman.cli import Command, register, Output


@register
class {pascal}Command(Command):
    """Custom command: {snake}"""
    signature = "custom:{snake} {{--option=}}"
    description = "Custom {snake} command"
    
    def handle(self):
        """Execute the command"""
        option = self.option("option", "default")
        
        Output.info(f"Running {snake} command with option={{option}}")
        
        # TODO: Implement command logic
        
        Output.success("{pascal} command completed!")
'''
        
        PathManager.write_file(path, content)
        Output.success(f"Command '{pascal}' created at {path}")
        Output.info(f"Usage: fastman custom:{snake}")


@register
class ListCommand(Command):
    signature = "list"
    description = "Show all available commands"
    
    def handle(self):
        Output.banner()
        
        # Group commands by category
        categories = {
            "Project": [],
            "Scaffolding": [],
            "Database": [],
            "Testing": [],
            "Configuration": [],
            "Utilities": []
        }
        
        for name, cls in sorted(COMMAND_REGISTRY.items()):
            sig = cls.signature.ljust(35)
            desc = cls.description
            
            # Categorize
            if name in ["new", "serve"]:
                categories["Project"].append((sig, desc))
            elif name.startswith("make:"):
                categories["Scaffolding"].append((sig, desc))
            elif name.startswith("migrate") or name.startswith("db:") or name == "make:migration":
                categories["Database"].append((sig, desc))
            elif name.startswith("make:test"):
                categories["Testing"].append((sig, desc))
            elif name.startswith("config:") or name.startswith("generate:") or name == "install:auth":
                categories["Configuration"].append((sig, desc))
            else:
                categories["Utilities"].append((sig, desc))
        
        # Display by category
        for category, commands in categories.items():
            if commands:
                Output.echo(f"\n{category}", Style.BOLD + Style.CYAN)
                Output.echo("=" * 80)
                for sig, desc in commands:
                    if HAS_RICH:
                        console.print(f"  [green]{sig}[/green] {desc}")
                    else:
                        print(f"  {Style.GREEN}{sig}{Style.RESET} {desc}")
        
        Output.echo("\n" + "=" * 80)
        Output.info(f"Fastman v{__version__} - The Complete FastAPI CLI")
        Output.info("For more info: fastman <command> --help")
        Output.echo("\nQuick Start:", Style.BOLD)
        Output.echo("  fastman new myproject      Create new project", Style.CYAN)
        Output.echo("  cd myproject               Navigate to project", Style.CYAN)
        Output.echo("  fastman serve              Start dev server", Style.CYAN)


@register
class VersionCommand(Command):
    signature = "version"
    description = "Show Fastman version"
    
    def handle(self):
        Output.echo(f"Fastman v{__version__}", Style.BOLD)
        Output.info("The Complete FastAPI CLI Framework")
        Output.echo("License: MIT", Style.CYAN)
        Output.echo("Repository: https://github.com/fastman/fastman", Style.CYAN)
        
        # Show Python version
        py_version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
        Output.echo(f"Python: {py_version}", Style.CYAN)
        
        # Show package manager
        manager, _ = PackageManager.detect()
        Output.echo(f"Package Manager: {manager}", Style.CYAN)


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


@register
class DocsCommand(Command):
    signature = "docs {--open}"
    description = "Show documentation or open in browser"
    
    def handle(self):
        should_open = self.flag("open")
        
        if should_open:
            import webbrowser
            url = "https://fastman.dev/docs"
            Output.info(f"Opening {url}...")
            webbrowser.open(url)
        else:
            Output.echo("\n📚 Fastman Documentation", Style.BOLD + Style.CYAN)
            Output.echo("=" * 80)
            Output.echo("\nQuick Start:")
            Output.echo("  1. fastman new myproject", Style.GREEN)
            Output.echo("  2. cd myproject", Style.GREEN)
            Output.echo("  3. fastman serve", Style.GREEN)
            
            Output.echo("\nCommon Commands:")
            Output.echo("  make:feature {name}  - Create vertical slice with CRUD", Style.CYAN)
            Output.echo("  make:api {name}      - Create lightweight endpoint", Style.CYAN)
            Output.echo("  make:migration {msg} - Create database migration", Style.CYAN)
            Output.echo("  migrate              - Run migrations", Style.CYAN)
            Output.echo("  route:list           - List all routes", Style.CYAN)
            
            Output.echo("\nDocumentation: https://fastman.dev/docs")
            Output.echo("Repository: https://github.com/fastman/fastman")
            Output.echo("=" * 80)


@register
class InspectCommand(Command):
    signature = "inspect {type} {name}"
    description = "Inspect project component (model, route, feature)"
    
    def handle(self):
        comp_type = self.argument(0)
        comp_name = self.argument(1)
        
        if not comp_type or not comp_name:
            Output.error("Usage: fastman inspect {type} {name}")
            Output.info("Types: model, feature, api, route")
            return
        
        sys.path.insert(0, str(Path.cwd()))
        
        if comp_type == "feature":
            self._inspect_feature(comp_name)
        elif comp_type == "api":
            self._inspect_api(comp_name)
        elif comp_type == "model":
            self._inspect_model(comp_name)
        else:
            Output.error(f"Unknown type: {comp_type}")
    
    def _inspect_feature(self, name: str):
        """Inspect a feature"""
        snake = NameValidator.to_snake_case(name)
        path = Path("app/features") / snake
        
        if not path.exists():
            Output.error(f"Feature '{snake}' not found")
            return
        
        Output.echo(f"\n📦 Feature: {snake}", Style.BOLD + Style.CYAN)
        Output.echo("=" * 80)
        
        files = {
            "models.py": "Database Models",
            "schemas.py": "Pydantic Schemas",
            "service.py": "Business Logic",
            "router.py": "API Routes"
        }
        
        for file_name, description in files.items():
            file_path = path / file_name
            if file_path.exists():
                size = file_path.stat().st_size
                Output.echo(f"  ✓ {file_name.ljust(15)} - {description} ({size} bytes)", Style.GREEN)
            else:
                Output.echo(f"  ✗ {file_name.ljust(15)} - {description}", Style.RED)
        
        # Try to load router and show endpoints
        try:
            module = importlib.import_module(f"app.features.{snake}.router")
            if hasattr(module, "router"):
                router = module.router
                Output.echo(f"\n  Endpoints:", Style.BOLD)
                for route in router.routes:
                    methods = ",".join(getattr(route, "methods", []))
                    path = getattr(route, "path", "")
                    Output.echo(f"    {methods.ljust(10)} {path}", Style.CYAN)
        except:
            pass
    
    def _inspect_api(self, name: str):
        """Inspect an API"""
        snake = NameValidator.to_snake_case(name)
        path = Path("app/api") / snake
        
        if not path.exists():
            Output.error(f"API '{snake}' not found")
            return
        
        Output.echo(f"\n🔌 API: {snake}", Style.BOLD + Style.CYAN)
        Output.echo("=" * 80)
        
        router_path = path / "router.py"
        schema_path = path / "schema.py"
        
        if router_path.exists():
            Output.echo(f"  Type: REST API", Style.GREEN)
        elif schema_path.exists():
            Output.echo(f"  Type: GraphQL API", Style.GREEN)
    
    def _inspect_model(self, name: str):
        """Inspect a model"""
        snake = NameValidator.to_snake_case(name)
        pascal = NameValidator.to_pascal_case(name)
        
        try:
            module = importlib.import_module(f"app.models.{snake}")
            model_class = getattr(module, pascal)
            
            Output.echo(f"\n🗄️  Model: {pascal}", Style.BOLD + Style.CYAN)
            Output.echo("=" * 80)
            Output.echo(f"  Table: {model_class.__tablename__}", Style.GREEN)
            Output.echo(f"  Columns:", Style.BOLD)
            
            for column in model_class.__table__.columns:
                col_type = str(column.type)
                nullable = "NULL" if column.nullable else "NOT NULL"
                pk = "PRIMARY KEY" if column.primary_key else ""
                Output.echo(f"    {column.name.ljust(20)} {col_type.ljust(15)} {nullable} {pk}", Style.CYAN)
        
        except Exception as e:
            Output.error(f"Failed to inspect model: {e}")


@register
class OptimizeCommand(Command):
    signature = "optimize {--check}"
    description = "Optimize project (remove unused imports, format code)"
    
    def handle(self):
        check_only = self.flag("check")
        
        if check_only:
            Output.info("Checking for optimization opportunities...")
        else:
            Output.info("Optimizing project...")
        
        # Check for common tools
        tools = {
            "black": "Code formatting",
            "isort": "Import sorting",
            "autoflake": "Remove unused imports"
        }
        
        missing_tools = []
        for tool, desc in tools.items():
            if not shutil.which(tool):
                missing_tools.append(tool)
        
        if missing_tools:
            Output.warn(f"Missing tools: {', '.join(missing_tools)}")
            if Output.confirm("Install optimization tools?"):
                PackageManager.install(missing_tools + ["--dev"] if PackageManager.detect()[0] != "pip" else missing_tools)
        
        # Run optimization
        app_path = Path("app")
        if not app_path.exists():
            Output.error("Not in a Fastman project")
            return
        
        if not check_only:
            # Format with black
            if shutil.which("black"):
                Output.info("Formatting code with black...")
                subprocess.run(["black", "app/", "tests/"], capture_output=True)
            
            # Sort imports
            if shutil.which("isort"):
                Output.info("Sorting imports with isort...")
                subprocess.run(["isort", "app/", "tests/"], capture_output=True)
            
            # Remove unused imports
            if shutil.which("autoflake"):
                Output.info("Removing unused imports...")
                subprocess.run([
                    "autoflake",
                    "--remove-all-unused-imports",
                    "--recursive",
                    "--in-place",
                    "app/",
                    "tests/"
                ], capture_output=True)
            
            Output.success("Project optimized!")
        else:
            Output.info("Check complete")


@register
class BuildCommand(Command):
    signature = "build {--docker}"
    description = "Build project for production"
    
    def handle(self):
        use_docker = self.flag("docker")
        
        if use_docker:
            self._build_docker()
        else:
            self._build_standard()
    
    def _build_docker(self):
        """Build Docker image"""
        Output.info("Building Docker image...")
        
        # Create Dockerfile if it doesn't exist
        dockerfile = Path("Dockerfile")
        if not dockerfile.exists():
            content = '''FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Run migrations and start server
CMD ["sh", "-c", "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8000"]
'''
            PathManager.write_file(dockerfile, content)
            Output.success("Dockerfile created")
        
        # Build image
        project_name = Path.cwd().name
        try:
            subprocess.run([
                "docker", "build",
                "-t", f"{project_name}:latest",
                "."
            ], check=True)
            Output.success(f"Docker image built: {project_name}:latest")
        except subprocess.CalledProcessError:
            Output.error("Docker build failed")
    
    def _build_standard(self):
        """Standard build"""
        Output.info("Building project...")
        
        # Run tests
        if Path("tests").exists():
            Output.info("Running tests...")
            result = subprocess.run(["pytest", "tests/"], capture_output=True)
            if result.returncode != 0:
                Output.error("Tests failed")
                return
        
        # Check types (if mypy available)
        if shutil.which("mypy"):
            Output.info("Checking types...")
            subprocess.run(["mypy", "app/"], capture_output=True)
        
        Output.success("Build complete!")


# ============================================================================
# MAIN ENTRY POINT
# ============================================================================

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
            except Exception as e:
                logger.error(f"Failed to load custom command {module_name}: {e}")
    
    def run(self, args: List[str]):
        """Run CLI with arguments"""
        if not args or args[0] in ["-h", "--help"]:
            ListCommand([], self.context).handle()
            return
        
        command_name = args[0]
        command_args = args[1:]
        
        # Handle special flags
        if command_name == "--version" or command_name == "-v":
            VersionCommand([], self.context).handle()
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
                Output.error(f"Command failed: {e}")
                logger.exception(e)
                sys.exit(1)
        else:
            Output.error(f"Unknown command: {command_name}")
            Output.info("Run 'fastman list' to see available commands")
            sys.exit(1)


def main():
    """Main entry point"""
    try:
        cli = CLI()
        cli.run(sys.argv[1:])
    except Exception as e:
        Output.error(f"Fatal error: {e}")
        logger.exception(e)
        sys.exit(1)


if __name__ == "__main__":
    main()
