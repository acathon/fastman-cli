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
    description = "Install authentication scaffolding (jwt, oauth, keycloak, passkey)"
    help = """
Examples:
  fastman install:auth
  fastman install:auth --type=jwt
  fastman install:auth --type=oauth --provider=google
  fastman install:auth --type=keycloak
  fastman install:auth --type=passkey
"""

    def handle(self):
        auth_type = self.option("type", "jwt").lower()
        provider = self.option("provider")

        if auth_type == "jwt":
            self._install_jwt()
        elif auth_type == "oauth":
            self._install_oauth(provider)
        elif auth_type == "keycloak":
            self._install_keycloak()
        elif auth_type == "passkey":
            self._install_passkey()
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
        provider = provider or "google"
        Output.info(f"Installing OAuth authentication (provider: {provider})...")

        packages = ["authlib", "httpx", "python-multipart"]
        if not PackageManager.install(packages):
            Output.error("Failed to install dependencies")
            return

        # Create auth feature directory
        base = Path("app/features/auth")
        PathManager.ensure_dir(base)

        # Provider configurations
        providers = {
            "google": {
                "authorize_url": "https://accounts.google.com/o/oauth2/v2/auth",
                "access_token_url": "https://oauth2.googleapis.com/token",
                "userinfo_url": "https://www.googleapis.com/oauth2/v3/userinfo",
                "scopes": "openid email profile",
                "env_prefix": "GOOGLE",
            },
            "github": {
                "authorize_url": "https://github.com/login/oauth/authorize",
                "access_token_url": "https://github.com/login/oauth/access_token",
                "userinfo_url": "https://api.github.com/user",
                "scopes": "read:user user:email",
                "env_prefix": "GITHUB",
            },
            "discord": {
                "authorize_url": "https://discord.com/api/oauth2/authorize",
                "access_token_url": "https://discord.com/api/oauth2/token",
                "userinfo_url": "https://discord.com/api/users/@me",
                "scopes": "identify email",
                "env_prefix": "DISCORD",
            },
        }

        cfg = providers.get(provider, providers["google"])
        env_prefix = cfg["env_prefix"]

        # OAuth config module
        oauth_config_content = f'''"""OAuth configuration for {provider}"""
from authlib.integrations.starlette_client import OAuth
from starlette.config import Config as StarletteConfig
from app.core.config import settings

oauth = OAuth()

oauth.register(
    name="{provider}",
    client_id=settings.OAUTH_CLIENT_ID,
    client_secret=settings.OAUTH_CLIENT_SECRET,
    authorize_url="{cfg["authorize_url"]}",
    access_token_url="{cfg["access_token_url"]}",
    userinfo_endpoint="{cfg["userinfo_url"]}",
    client_kwargs={{"scope": "{cfg["scopes"]}"}},
)
'''

        # OAuth models
        oauth_models_content = '''"""OAuth user models"""
from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sqlalchemy.sql import func
from app.core.database import Base


class User(Base):
    """User model for OAuth authentication"""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    name = Column(String(200))
    avatar_url = Column(String(500))
    oauth_provider = Column(String(50), nullable=False)
    oauth_id = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    def __repr__(self):
        return f"<User(id={self.id}, email={self.email}, provider={self.oauth_provider})>"
'''

        # OAuth schemas
        oauth_schemas_content = '''"""OAuth authentication schemas"""
from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime


class UserRead(BaseModel):
    """User response schema"""
    id: int
    email: EmailStr
    name: Optional[str] = None
    avatar_url: Optional[str] = None
    oauth_provider: str
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class OAuthCallback(BaseModel):
    """OAuth callback data"""
    code: str
    state: Optional[str] = None
'''

        # OAuth service
        oauth_service_content = '''"""OAuth authentication service"""
from sqlalchemy.orm import Session
from typing import Optional
from . import models


class OAuthService:
    """OAuth service layer"""

    @staticmethod
    def get_user_by_email(db: Session, email: str) -> Optional[models.User]:
        """Get user by email"""
        return db.query(models.User).filter(models.User.email == email).first()

    @staticmethod
    def get_user_by_oauth_id(db: Session, provider: str, oauth_id: str) -> Optional[models.User]:
        """Get user by OAuth provider and ID"""
        return db.query(models.User).filter(
            models.User.oauth_provider == provider,
            models.User.oauth_id == oauth_id
        ).first()

    @staticmethod
    def create_or_update_user(db: Session, provider: str, user_info: dict) -> models.User:
        """Create or update user from OAuth data"""
        oauth_id = str(user_info.get("sub") or user_info.get("id"))
        email = user_info.get("email")

        user = OAuthService.get_user_by_oauth_id(db, provider, oauth_id)

        if user:
            user.name = user_info.get("name", user.name)
            user.avatar_url = user_info.get("picture") or user_info.get("avatar_url")
            user.email = email or user.email
        else:
            user = models.User(
                email=email,
                name=user_info.get("name"),
                avatar_url=user_info.get("picture") or user_info.get("avatar_url"),
                oauth_provider=provider,
                oauth_id=oauth_id,
            )
            db.add(user)

        db.commit()
        db.refresh(user)
        return user
'''

        # OAuth router
        oauth_router_content = f'''"""OAuth authentication routes"""
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from datetime import timedelta
from app.core.database import get_db
from .oauth_config import oauth
from . import schemas, service

router = APIRouter(prefix="/auth", tags=["Authentication"])

PROVIDER = "{provider}"


@router.get("/login")
async def oauth_login(request: Request):
    """Redirect to OAuth provider login page"""
    redirect_uri = str(request.url_for("oauth_callback"))
    return await oauth.{provider}.authorize_redirect(request, redirect_uri)


@router.get("/callback", name="oauth_callback")
async def oauth_callback(request: Request, db: Session = Depends(get_db)):
    """Handle OAuth provider callback"""
    try:
        token = await oauth.{provider}.authorize_access_token(request)
    except Exception:
        raise HTTPException(status_code=401, detail="OAuth authentication failed")

    user_info = token.get("userinfo")
    if user_info is None:
        user_info = await oauth.{provider}.userinfo(token=token)

    user = service.OAuthService.create_or_update_user(db, PROVIDER, dict(user_info))

    return schemas.UserRead.model_validate(user)


@router.get("/me", response_model=schemas.UserRead)
async def get_me(request: Request, db: Session = Depends(get_db)):
    """Get current user info (requires session)"""
    user_email = request.session.get("user_email")
    if not user_email:
        raise HTTPException(status_code=401, detail="Not authenticated")

    user = service.OAuthService.get_user_by_email(db, user_email)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return user


@router.get("/logout")
async def logout(request: Request):
    """Logout user"""
    request.session.clear()
    return {{"message": "Logged out successfully"}}
'''

        # Write all files
        PathManager.write_file(base / "oauth_config.py", oauth_config_content)
        PathManager.write_file(base / "models.py", oauth_models_content)
        PathManager.write_file(base / "schemas.py", oauth_schemas_content)
        PathManager.write_file(base / "service.py", oauth_service_content)
        PathManager.write_file(base / "router.py", oauth_router_content)

        # Update .env
        env_path = Path(".env")
        if env_path.exists():
            env_content = env_path.read_text(encoding='utf-8')
            if "OAUTH_CLIENT_ID" not in env_content:
                oauth_env = f"""
# OAuth ({provider})
OAUTH_CLIENT_ID=your-{provider}-client-id
OAUTH_CLIENT_SECRET=your-{provider}-client-secret
"""
                env_content += oauth_env
                env_path.write_text(env_content, encoding='utf-8')
                Output.info("Updated .env with OAuth credentials")

        Output.success(f"OAuth authentication installed ({provider})!")
        Output.info("\nFiles created:")
        Output.echo("  app/features/auth/oauth_config.py - OAuth config", Style.GREEN)
        Output.echo("  app/features/auth/models.py - User model", Style.GREEN)
        Output.echo("  app/features/auth/schemas.py - Pydantic schemas", Style.GREEN)
        Output.echo("  app/features/auth/service.py - OAuth service", Style.GREEN)
        Output.echo("  app/features/auth/router.py - OAuth routes", Style.GREEN)
        Output.info("\nEndpoints created:")
        Output.echo("  GET  /auth/login - Redirect to provider", Style.GREEN)
        Output.echo("  GET  /auth/callback - OAuth callback", Style.GREEN)
        Output.echo("  GET  /auth/me - Current user info", Style.GREEN)
        Output.echo("  GET  /auth/logout - Logout", Style.GREEN)
        Output.info("\nNext steps:")
        Output.echo(f"  1. Create a {provider} OAuth app and get Client ID/Secret", Style.CYAN)
        Output.echo("  2. Update .env with your credentials", Style.CYAN)
        Output.echo("  3. Run: fastman make:migration 'add users table'", Style.CYAN)
        Output.echo("  4. Run: fastman database:migrate", Style.CYAN)
        Output.echo("  5. Add SessionMiddleware to app/main.py:", Style.CYAN)
        Output.echo('     from starlette.middleware.sessions import SessionMiddleware', Style.YELLOW)
        Output.echo('     app.add_middleware(SessionMiddleware, secret_key=settings.SECRET_KEY)', Style.YELLOW)

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

    def _install_passkey(self):
        """Install WebAuthn/Passkey authentication (passwordless)"""
        Output.info("Installing Passkey (WebAuthn) authentication...")

        packages = [
            "py-webauthn>=2.0.0",
            "pyjwt",
            "python-multipart",
        ]

        if not PackageManager.install(packages):
            Output.error("Failed to install dependencies")
            return

        base = Path("app/features/auth")
        PathManager.ensure_dir(base)

        # Passkey models
        models_content = '''"""Passkey authentication models"""
from sqlalchemy import Column, Integer, String, Boolean, DateTime, LargeBinary, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base


class User(Base):
    """User model for passkey authentication"""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    username = Column(String(100), unique=True, index=True, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    credentials = relationship("PasskeyCredential", back_populates="user", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<User(id={self.id}, email={self.email})>"


class PasskeyCredential(Base):
    """Stored WebAuthn credential"""
    __tablename__ = "passkey_credentials"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    credential_id = Column(LargeBinary, unique=True, nullable=False)
    public_key = Column(LargeBinary, nullable=False)
    sign_count = Column(Integer, default=0)
    device_name = Column(String(200), default="Unknown device")
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="credentials")

    def __repr__(self):
        return f"<PasskeyCredential(id={self.id}, user_id={self.user_id})>"
'''

        # Passkey schemas
        schemas_content = '''"""Passkey authentication schemas"""
from pydantic import BaseModel, EmailStr, Field
from typing import Optional, Any
from datetime import datetime


class UserCreate(BaseModel):
    """Schema for user registration"""
    email: EmailStr
    username: str = Field(..., min_length=3, max_length=100)


class UserRead(BaseModel):
    """Schema for user response"""
    id: int
    email: EmailStr
    username: str
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class Token(BaseModel):
    """Token response schema"""
    access_token: str
    token_type: str = "bearer"


class RegistrationOptionsRequest(BaseModel):
    """Request to start passkey registration"""
    email: EmailStr
    username: str = Field(..., min_length=3, max_length=100)


class RegistrationVerifyRequest(BaseModel):
    """Verify passkey registration"""
    email: str
    credential: Any


class AuthenticationOptionsRequest(BaseModel):
    """Request to start passkey authentication"""
    email: Optional[EmailStr] = None


class AuthenticationVerifyRequest(BaseModel):
    """Verify passkey authentication"""
    credential: Any


class CredentialRead(BaseModel):
    """Credential info response"""
    id: int
    device_name: str
    created_at: datetime

    class Config:
        from_attributes = True
'''

        # Passkey service
        service_content = '''"""Passkey authentication service"""
import json
import secrets
from typing import Optional
from sqlalchemy.orm import Session
import webauthn
from webauthn.helpers.structs import (
    AuthenticatorSelectionCriteria,
    ResidentKeyRequirement,
    UserVerificationRequirement,
    PublicKeyCredentialDescriptor,
)
from webauthn.helpers.cose import COSEAlgorithmIdentifier
from webauthn.helpers import bytes_to_base64url, base64url_to_bytes
from app.core.config import settings
from . import models

# In-memory challenge store (use Redis in production)
_challenges: dict[str, bytes] = {}


def _get_rp_id() -> str:
    """Get relying party ID from settings"""
    return getattr(settings, "PASSKEY_RP_ID", "localhost")


def _get_rp_name() -> str:
    """Get relying party name from settings"""
    return getattr(settings, "PASSKEY_RP_NAME", "Fastman App")


def _get_origin() -> str:
    """Get expected origin from settings"""
    return getattr(settings, "PASSKEY_ORIGIN", "http://localhost:8000")


class PasskeyService:
    """WebAuthn/Passkey service"""

    @staticmethod
    def get_user_by_email(db: Session, email: str) -> Optional[models.User]:
        return db.query(models.User).filter(models.User.email == email).first()

    @staticmethod
    def create_user(db: Session, email: str, username: str) -> models.User:
        user = models.User(email=email, username=username)
        db.add(user)
        db.commit()
        db.refresh(user)
        return user

    @staticmethod
    def generate_registration_options(db: Session, email: str, username: str) -> dict:
        """Generate WebAuthn registration options"""
        user = PasskeyService.get_user_by_email(db, email)
        if not user:
            user = PasskeyService.create_user(db, email, username)

        existing_credentials = [
            PublicKeyCredentialDescriptor(id=cred.credential_id)
            for cred in user.credentials
        ]

        options = webauthn.generate_registration_options(
            rp_id=_get_rp_id(),
            rp_name=_get_rp_name(),
            user_id=str(user.id).encode(),
            user_name=user.email,
            user_display_name=user.username,
            exclude_credentials=existing_credentials,
            authenticator_selection=AuthenticatorSelectionCriteria(
                resident_key=ResidentKeyRequirement.PREFERRED,
                user_verification=UserVerificationRequirement.PREFERRED,
            ),
            supported_pub_key_algs=[
                COSEAlgorithmIdentifier.ECDSA_SHA_256,
                COSEAlgorithmIdentifier.RSASSA_PKCS1_v1_5_SHA_256,
            ],
        )

        _challenges[email] = options.challenge
        return json.loads(webauthn.options_to_json(options))

    @staticmethod
    def verify_registration(db: Session, email: str, credential: dict) -> models.PasskeyCredential:
        """Verify and store WebAuthn registration"""
        challenge = _challenges.pop(email, None)
        if not challenge:
            raise ValueError("Registration challenge expired or not found")

        verification = webauthn.verify_registration_response(
            credential=credential,
            expected_challenge=challenge,
            expected_rp_id=_get_rp_id(),
            expected_origin=_get_origin(),
        )

        user = PasskeyService.get_user_by_email(db, email)
        if not user:
            raise ValueError("User not found")

        passkey = models.PasskeyCredential(
            user_id=user.id,
            credential_id=verification.credential_id,
            public_key=verification.credential_public_key,
            sign_count=verification.sign_count,
            device_name=credential.get("device_name", "Unknown device"),
        )
        db.add(passkey)
        db.commit()
        db.refresh(passkey)
        return passkey

    @staticmethod
    def generate_authentication_options(db: Session, email: Optional[str] = None) -> dict:
        """Generate WebAuthn authentication options"""
        allow_credentials = []

        if email:
            user = PasskeyService.get_user_by_email(db, email)
            if user:
                allow_credentials = [
                    PublicKeyCredentialDescriptor(id=cred.credential_id)
                    for cred in user.credentials
                ]

        options = webauthn.generate_authentication_options(
            rp_id=_get_rp_id(),
            allow_credentials=allow_credentials,
            user_verification=UserVerificationRequirement.PREFERRED,
        )

        key = email or "__discoverable__"
        _challenges[key] = options.challenge
        return json.loads(webauthn.options_to_json(options))

    @staticmethod
    def verify_authentication(db: Session, credential: dict, email: Optional[str] = None) -> models.User:
        """Verify WebAuthn authentication"""
        credential_id = base64url_to_bytes(credential["id"])

        stored = db.query(models.PasskeyCredential).filter(
            models.PasskeyCredential.credential_id == credential_id
        ).first()

        if not stored:
            raise ValueError("Credential not found")

        key = email or "__discoverable__"
        challenge = _challenges.pop(key, None)
        if not challenge:
            raise ValueError("Authentication challenge expired or not found")

        verification = webauthn.verify_authentication_response(
            credential=credential,
            expected_challenge=challenge,
            expected_rp_id=_get_rp_id(),
            expected_origin=_get_origin(),
            credential_public_key=stored.public_key,
            credential_current_sign_count=stored.sign_count,
        )

        stored.sign_count = verification.new_sign_count
        db.commit()

        return stored.user
'''

        # Passkey security (JWT token generation for session)
        security_content = '''"""Passkey session token utilities"""
from datetime import datetime, timedelta, timezone
from typing import Optional
import jwt
from app.core.config import settings

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create JWT session token after passkey auth"""
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=ALGORITHM)


def decode_token(token: str) -> Optional[dict]:
    """Decode session token"""
    try:
        return jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM])
    except jwt.InvalidTokenError:
        return None
'''

        # Passkey dependencies
        dependencies_content = '''"""Passkey authentication dependencies"""
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from app.core.database import get_db
from . import models
from .security import decode_token

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/passkey/authenticate/verify", auto_error=False)


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> models.User:
    """Get current authenticated user from passkey session token"""
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )

    payload = decode_token(token)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id = payload.get("sub")
    if user_id is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    user = db.query(models.User).filter(models.User.id == int(user_id)).first()
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")

    return user


async def get_current_active_user(
    current_user: models.User = Depends(get_current_user)
) -> models.User:
    """Get current active user"""
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user
'''

        # Passkey router
        router_content = '''"""Passkey (WebAuthn) authentication routes"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from . import schemas, service
from .security import create_access_token
from .dependencies import get_current_active_user

router = APIRouter(prefix="/auth/passkey", tags=["Passkey Authentication"])


@router.post("/register/options")
def registration_options(
    data: schemas.RegistrationOptionsRequest,
    db: Session = Depends(get_db)
):
    """Get WebAuthn registration options (step 1)"""
    try:
        options = service.PasskeyService.generate_registration_options(
            db, data.email, data.username
        )
        return options
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/register/verify")
def registration_verify(
    data: schemas.RegistrationVerifyRequest,
    db: Session = Depends(get_db)
):
    """Verify passkey registration (step 2)"""
    try:
        service.PasskeyService.verify_registration(db, data.email, data.credential)
        return {"status": "ok", "message": "Passkey registered successfully"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/authenticate/options")
def authentication_options(
    data: schemas.AuthenticationOptionsRequest = None,
    db: Session = Depends(get_db)
):
    """Get WebAuthn authentication options (step 1)"""
    email = data.email if data else None
    options = service.PasskeyService.generate_authentication_options(db, email)
    return options


@router.post("/authenticate/verify", response_model=schemas.Token)
def authentication_verify(
    data: schemas.AuthenticationVerifyRequest,
    db: Session = Depends(get_db)
):
    """Verify passkey authentication and return session token (step 2)"""
    try:
        user = service.PasskeyService.verify_authentication(db, data.credential)
        token = create_access_token(data={"sub": str(user.id)})
        return {"access_token": token, "token_type": "bearer"}
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))


@router.get("/me", response_model=schemas.UserRead)
async def get_me(current_user=Depends(get_current_active_user)):
    """Get current user info"""
    return current_user


@router.get("/credentials", response_model=list[schemas.CredentialRead])
async def list_credentials(
    current_user=Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """List all registered passkeys for current user"""
    return current_user.credentials


@router.delete("/credentials/{credential_id}")
async def delete_credential(
    credential_id: int,
    current_user=Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Remove a registered passkey"""
    from . import models
    cred = db.query(models.PasskeyCredential).filter(
        models.PasskeyCredential.id == credential_id,
        models.PasskeyCredential.user_id == current_user.id,
    ).first()
    if not cred:
        raise HTTPException(status_code=404, detail="Credential not found")

    db.delete(cred)
    db.commit()
    return {"status": "ok", "message": "Passkey removed"}
'''

        # Write all files
        PathManager.write_file(base / "models.py", models_content)
        PathManager.write_file(base / "schemas.py", schemas_content)
        PathManager.write_file(base / "service.py", service_content)
        PathManager.write_file(base / "security.py", security_content)
        PathManager.write_file(base / "dependencies.py", dependencies_content)
        PathManager.write_file(base / "router.py", router_content)

        # Update .env
        env_path = Path(".env")
        if env_path.exists():
            env_content = env_path.read_text(encoding='utf-8')
            if "PASSKEY_RP_ID" not in env_content:
                passkey_env = """
# Passkey / WebAuthn
PASSKEY_RP_ID=localhost
PASSKEY_RP_NAME=Fastman App
PASSKEY_ORIGIN=http://localhost:8000
"""
                env_content += passkey_env
                env_path.write_text(env_content, encoding='utf-8')
                Output.info("Updated .env with Passkey settings")

        Output.success("Passkey (WebAuthn) authentication installed!")
        Output.info("\nNo passwords needed! Users authenticate with:")
        Output.echo("  - Fingerprint", Style.GREEN)
        Output.echo("  - Face ID", Style.GREEN)
        Output.echo("  - Hardware security key (YubiKey)", Style.GREEN)
        Output.echo("  - Device PIN", Style.GREEN)
        Output.info("\nEndpoints created:")
        Output.echo("  POST /auth/passkey/register/options - Start registration", Style.GREEN)
        Output.echo("  POST /auth/passkey/register/verify - Verify registration", Style.GREEN)
        Output.echo("  POST /auth/passkey/authenticate/options - Start login", Style.GREEN)
        Output.echo("  POST /auth/passkey/authenticate/verify - Verify login", Style.GREEN)
        Output.echo("  GET  /auth/passkey/me - Current user", Style.GREEN)
        Output.echo("  GET  /auth/passkey/credentials - List passkeys", Style.GREEN)
        Output.echo("  DELETE /auth/passkey/credentials/{id} - Remove passkey", Style.GREEN)
        Output.info("\nNext steps:")
        Output.echo("  1. Run: fastman make:migration 'add users and passkeys tables'", Style.CYAN)
        Output.echo("  2. Run: fastman database:migrate", Style.CYAN)
        Output.echo("  3. Update .env with your domain (RP_ID, ORIGIN)", Style.CYAN)
        Output.echo("  4. Implement the WebAuthn JS client (see browser API docs)", Style.CYAN)
