---
sidebar_position: 1
---

# Production Deployment

Deploy your Fastman application to production.

## Pre-Deployment Checklist

Before deploying, ensure you:

- [ ] Set `DEBUG=false` in production
- [ ] Generate a secure `SECRET_KEY`
- [ ] Configure production database URL
- [ ] Run all migrations
- [ ] Set up proper logging

## Docker Deployment

### Build the Image

```bash
fastman build --docker
```

Or manually with the generated Dockerfile:

```bash
docker build -t my-api:latest .
```

### Run the Container

```bash
docker run -d \
  -p 8000:8000 \
  -e DATABASE_URL=postgresql://user:pass@host/db \
  -e SECRET_KEY=your-production-secret \
  my-api:latest
```

### Docker Compose

```yaml
# docker-compose.yml
version: '3.8'

services:
  api:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://postgres:password@db:5432/app
      - SECRET_KEY=${SECRET_KEY}
    depends_on:
      - db

  db:
    image: postgres:15
    environment:
      POSTGRES_DB: app
      POSTGRES_PASSWORD: password
    volumes:
      - postgres_data:/var/lib/postgresql/data

volumes:
  postgres_data:
```

## Performance Optimization

### Cache Configuration

Cache your environment configuration for faster startup:

```bash
fastman config:cache
```

To clear:

```bash
fastman config:clear
```

### Code Optimization

Remove unused imports and format code:

```bash
fastman optimize
```

### Clear Cache

Remove Python bytecode cache:

```bash
fastman cache:clear
```

## Cloud Platforms

### Railway / Render

Most platforms auto-detect Python projects. Ensure your `Procfile`:

```
web: uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

### AWS / GCP / Azure

Use the Docker deployment method with your cloud's container service.

## Reverse Proxy

Example Nginx configuration:

```nginx
server {
    listen 80;
    server_name api.example.com;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```
