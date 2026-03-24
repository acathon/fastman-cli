---
sidebar_position: 10
---

# Deployment

An overview of how to deploy your Fastman-generated FastAPI application to production.

## Pre-Deployment Checklist

Before deploying, make sure you've completed these steps:

- [ ] Set `DEBUG=false` in your production environment
- [ ] Generate a secure `SECRET_KEY` with `fastman generate:key`
- [ ] Configure a production database URL (not SQLite)
- [ ] Run all pending migrations: `fastman database:migrate`
- [ ] Run your test suite: `fastman build`
- [ ] Set up proper logging and monitoring

## Quick Deploy Options

| Platform | Difficulty | Best For | Free Tier |
|----------|------------|----------|-----------|
| [Railway](https://railway.app) | Easy | Quick deploys, small projects | Yes |
| [Render](https://render.com) | Easy | Full-stack apps with managed databases | Yes |
| [Fly.io](https://fly.io) | Medium | Edge deployment, global distribution | Yes |
| [AWS ECS](https://aws.amazon.com) | Advanced | Enterprise scale, full AWS ecosystem | No |
| [DigitalOcean App Platform](https://digitalocean.com) | Medium | Simple container hosting | No |

## Environment Setup

### Multi-Environment Files

Fastman generates environment files for each stage:

| File | Purpose |
|------|---------|
| `.env` | Fallback (used if no environment-specific file found) |
| `.env.development` | Local development settings |
| `.env.staging` | Staging environment settings |
| `.env.production` | Production environment settings |

The active file is selected via the `--env` flag:

```bash
# Use development settings
fastman serve --env=development

# Use staging settings
fastman serve --env=staging

# Use production settings (or just `fastman serve` — auto-detected)
fastman serve --env=production
```

When no `--env` flag is provided, Fastman auto-detects `.env.production` if it exists, otherwise falls back to `.env`.

### Production Configuration

Your `.env.production` (or deployment platform env vars) should include:

```env
ENVIRONMENT=production
DEBUG=false
SECRET_KEY=<your-production-secret-key>

# Database
DB_HOST=production-db-host
DB_PORT=5432
DB_USER=prod_user
DB_PASSWORD=<strong-password>
DB_NAME=myapp

# Optional CORS
CORS_ORIGINS=https://myapp.com,https://www.myapp.com
```

For cloud deployments, prefer your platform's environment variable management over `.env` files.

### Generate a Secure Secret Key

```bash
fastman generate:key --show
```

Copy the output and set it as the `SECRET_KEY` environment variable in your deployment platform.

:::warning
Never commit secrets to version control. Use your deployment platform's environment variable management (Railway variables, Render env groups, AWS Secrets Manager, etc.).
:::

## Health Checks

Most container orchestrators and deployment platforms need a health check endpoint. Add one to your `app/main.py`:

```python
@app.get("/health")
def health_check():
    return {"status": "healthy"}
```

This allows load balancers and orchestrators to verify your application is running and responsive.

## Procfile

For platforms that auto-detect Python projects (Railway, Render, Heroku-compatible), create a `Procfile` in your project root:

```
web: python -m uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

## Next Steps

See the [Production Build](./advanced/production-build) guide for detailed Docker deployment, performance optimization, and reverse proxy configuration.
