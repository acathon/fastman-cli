"""
Scaffolding commands for generating code.
"""
from pathlib import Path
from .base import Command, register
from ..console import Output, Style
from ..utils import NameValidator, PathManager


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
        # NOTE: Using 'def' instead of 'async def' because SQLAlchemy session operations are synchronous.
        # This prevents blocking the main event loop.
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
def list_{snake}s(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """Get all {snake}s"""
    return service.{pascal}Service.get_all(db, skip=skip, limit=limit)


@router.get("/{{id}}", response_model=schemas.{pascal}Read)
def get_{snake}(id: int, db: Session = Depends(get_db)):
    """Get {snake} by ID"""
    obj = service.{pascal}Service.get_by_id(db, id)
    if not obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"{pascal} not found"
        )
    return obj


@router.post("/", response_model=schemas.{pascal}Read, status_code=status.HTTP_201_CREATED)
def create_{snake}(
    data: schemas.{pascal}Create,
    db: Session = Depends(get_db)
):
    """Create new {snake}"""
    return service.{pascal}Service.create(db, data)


@router.put("/{{id}}", response_model=schemas.{pascal}Read)
def update_{snake}(
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
def delete_{snake}(id: int, db: Session = Depends(get_db)):
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
def list_{snake}s(db: Session = Depends(get_db)):
    """Get all {snake}s"""
    return service.{pascal}Service.get_all(db)
'''

        # Write files
        PathManager.write_file(base / "models.py", model_content)
        PathManager.write_file(base / "schemas.py", schema_content)
        PathManager.write_file(base / "service.py", service_content)
        PathManager.write_file(base / "router.py", router_content)

        from .. import __version__
        Output.banner(__version__)
        Output.section("Feature Created", f"{snake} at app/features/{snake}/")
        
        files_created = [
            ("models.py", "Database model with SQLAlchemy"),
            ("schemas.py", "Pydantic schemas for validation"),
            ("service.py", "Business logic layer"),
            ("router.py", f"{'CRUD' if crud else 'Basic'} API endpoints"),
        ]
        
        Output.listing(files_created, title="Files Created")
        
        if crud:
            Output.section("Generated Endpoints")
            endpoints = [
                (f"GET    /{snake}s", "List all items"),
                (f"GET    /{snake}s/{{id}}", "Get single item"),
                (f"POST   /{snake}s", "Create new item"),
                (f"PUT    /{snake}s/{{id}}", "Update item"),
                (f"DELETE /{snake}s/{{id}}", "Delete item"),
            ]
            Output.listing(endpoints)
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
def list_{snake}s():
    """List all {snake}s"""
    # TODO: Implement logic
    return []


@router.get("/{{id}}", response_model={pascal}Response)
def get_{snake}(id: int):
    """Get {snake} by ID"""
    # TODO: Implement logic
    return {pascal}Response(id=id, name="Example")
'''
            # Note: keeping async here as no DB calls are implied yet, but user should know.
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
            from ..utils import PackageManager
            PackageManager.install(["faker"])

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

from fastman import Command, register, Output


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
class MakeSchemaCommand(Command):
    signature = "make:schema {name}"
    description = "Create Pydantic schema"

    def handle(self):
        name = self.validate_name(self.argument(0), "Schema name is required")

        snake = NameValidator.to_snake_case(name)
        pascal = NameValidator.to_pascal_case(name)

        path = Path("app/schemas") / f"{snake}.py"

        if path.exists():
            Output.error(f"Schema '{snake}' already exists")
            return

        PathManager.ensure_dir(path.parent)

        content = f'''"""Pydantic schema for {pascal}"""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class {pascal}Base(BaseModel):
    """Base schema"""
    name: str = Field(..., min_length=1)
    description: Optional[str] = None


class {pascal}Create({pascal}Base):
    """Creation schema"""
    pass


class {pascal}Update(BaseModel):
    """Update schema"""
    name: Optional[str] = Field(None, min_length=1)


class {pascal}Read({pascal}Base):
    """Read schema"""
    id: int
    created_at: datetime

    class Config:
        from_attributes = True
'''

        PathManager.write_file(path, content)
        Output.success(f"Schema '{pascal}' created at {path}")
