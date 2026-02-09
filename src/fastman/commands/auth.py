"""
Authentication installation commands.
"""
from pathlib import Path
from .base import Command, register
from ..console import Output, Style
from ..utils import PackageManager, PathManager

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
def register(user_data: schemas.UserCreate, db: Session = Depends(get_db)):
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
def login(
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

    def _install_oauth(self, provider):
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

        # Verify project structure exists
        core_dir = Path("app/core")
        if not core_dir.exists():
            Output.error("Directory 'app/core' not found.")
            Output.info("Make sure you are in a Fastman project directory.")
            Output.info("Run 'fastman new <project-name>' to create a new project first.")
            return

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
        if not PathManager.write_file(keycloak_path, keycloak_config):
            Output.error(f"Failed to create {keycloak_path}")
            return

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
