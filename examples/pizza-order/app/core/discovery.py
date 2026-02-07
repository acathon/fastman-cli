"""Auto-discovery of routers and features"""
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
                            app.include_router(module.router)
                            logger.info(f"Registered API router: {item.name}")
                    except (ModuleNotFoundError, AttributeError) as e:
                        logger.error(f"Failed to load API {item.name}: {e}")
