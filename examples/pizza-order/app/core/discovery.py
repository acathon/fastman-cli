"""Auto-discovery of routers and features"""
import pkgutil
import importlib
from pathlib import Path
from fastapi import FastAPI, APIRouter
import logging

logger = logging.getLogger(__name__)

def _resolve_prefix(settings, version: str) -> str:
    """Resolve the API prefix from a version string (e.g. 'v1', 'v2')."""
    prefixes = {
        "v1": settings.API_V1_PREFIX,
        "v2": settings.API_V2_PREFIX,
    }
    return prefixes.get(version, settings.API_V1_PREFIX)


def discover_routers(app: FastAPI):
    """Discover and register all routers.

    Routers can declare their API version by setting a module-level attribute:

        api_version = "v2"   # mounts under /api/v2

    If omitted, defaults to "v1" (/api/v1).
    """
    from app.core.config import settings

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
                            version = getattr(module, "api_version", "v1")
                            prefix = _resolve_prefix(settings, version)
                            app.include_router(module.router, prefix=prefix)
                            logger.info(f"Registered feature router: {item.name} at {prefix}")
                    except (ModuleNotFoundError, AttributeError) as e:
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
                            version = getattr(module, "api_version", "v1")
                            prefix = _resolve_prefix(settings, version)
                            app.include_router(module.router, prefix=prefix)
                            logger.info(f"Registered API router: {item.name} at {prefix}")
                    except (ModuleNotFoundError, AttributeError) as e:
                        logger.error(f"Failed to load API {item.name}: {e}")
