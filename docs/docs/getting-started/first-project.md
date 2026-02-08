---
sidebar_position: 1
---

# Creating Your First Project

Let's build a REST API in 5 minutes.

## Create the Project

```bash
fastman new blog-api
```

You'll be prompted for options, or specify them directly:

```bash
fastman new blog-api --pattern=feature --database=postgresql --package=uv
```

### Available Options

| Option | Values | Default |
|--------|--------|---------|
| `--pattern` | `feature`, `api`, `layer` | `feature` |
| `--database` | `sqlite`, `postgresql`, `mysql`, `oracle`, `firebase` | `sqlite` |
| `--package` | `uv`, `poetry`, `pipenv`, `pip` | auto-detected |

## Project Structure

After creation, your project looks like this:

```
blog-api/
├── app/
│   ├── core/           # Configuration, database, dependencies
│   │   ├── config.py
│   │   ├── database.py
│   │   └── dependencies.py
│   ├── features/       # Feature modules (vertical slices)
│   └── main.py         # Application entry point
├── database/
│   ├── migrations/     # Alembic migrations
│   └── seeders/        # Database seeders
├── tests/              # Test files
├── .env                # Environment variables
└── pyproject.toml      # Dependencies
```

## Start the Development Server

```bash
cd blog-api
fastman serve
```

Your API is now running at `http://localhost:8000`.

Visit `http://localhost:8000/docs` for the interactive Swagger documentation.

## Create Your First Feature

Let's add a posts feature with full CRUD:

```bash
fastman make:feature post --crud
```

This creates:

```
app/features/post/
├── __init__.py
├── models.py      # SQLAlchemy model
├── schemas.py     # Pydantic schemas
├── service.py     # Business logic
└── router.py      # API endpoints
```

## Run Migrations

```bash
# Create a migration
fastman make:migration "create posts table"

# Apply migrations
fastman database:migrate
```

## Test Your API

Open `http://localhost:8000/docs` and try the endpoints:

- `GET /posts` — List all posts
- `POST /posts` — Create a post
- `GET /posts/{id}` — Get a post
- `PUT /posts/{id}` — Update a post
- `DELETE /posts/{id}` — Delete a post

## Next Steps

- [Add authentication](../concepts/authentication)
- [Understand the architecture](../concepts/architecture)
- [Explore all commands](../commands/project)
