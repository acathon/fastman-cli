---
sidebar_position: 2
---

# Production & Docker

Fastman makes it easy to prepare your application for production.

## Building for Production

Run the `build` command to run tests and type checks:

```bash
fastman build
```

## Docker Support

Fastman can automatically generate a `Dockerfile` and build an image for you.

```bash
fastman build --docker
```

This will:
1.  Create a production-ready `Dockerfile` (if missing).
2.  Build the image using your project name.

### Generated Dockerfile

The generated Dockerfile is optimized for python 3.11-slim:

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Run migrations and start server
CMD ["sh", "-c", "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8000"]
```

## Configuration Caching

In production, parsing `.env` files can be slow. Use config caching to speed up boot time.

```bash
fastman config:cache
```

This creates a `config_cache.json` file that Fastman loads instantly.
