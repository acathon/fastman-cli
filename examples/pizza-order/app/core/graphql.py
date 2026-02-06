"""GraphQL schema setup"""
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
            except (ModuleNotFoundError, AttributeError) as e:
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
