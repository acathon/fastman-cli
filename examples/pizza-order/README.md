# pizza-order

FastAPI project generated with Fastman v0.1.0

**Pattern**: feature - Feature modules (vertical slices)
**Package Manager**: uv

## Getting Started

```bash
cd pizza-order

# Activate virtual environment (if created)
# uv handles venv automatically


# Install dependencies
uv sync

# Run development server
fastman serve

# View available commands
fastman list
```

## Project Structure

```
pizza-order/
├── app/
│   ├── core/          # Core configuration and utilities
│   ├── features/      # Feature modules (vertical slices)
│   ├── api/           # Lightweight API endpoints
│   └── models/        # Database models
├── tests/             # Test files
├── alembic/           # Database migrations
└── logs/              # Application logs
```

## Documentation

- API Documentation: http://localhost:8000/docs
- GraphQL Playground: http://localhost:8000/graphql

Generated with ❤️ by Fastman
