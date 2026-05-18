---
sidebar_position: 10
---

# Deployment

An overview of how to deploy your Fastman-generated FastAPI application to production.

## Pre-Deployment Checklist

Before deploying, make sure you've completed these steps:

- [ ] Set `DEBUG=false` in your production environment
- [ ] Generate a secure `SECRET_KEY` with `fastman config:appkey`
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

### Three env files, not four

Fastman 0.4.0+ scaffolds three environment files:

| File | Purpose |
|------|---------|
| `.env` | Fallback / local override (gitignored by default) |
| `.env.develop` | Local development settings |
| `.env.staging` | Staging environment settings |

There is intentionally **no `.env.production`**. Production secrets should
come from a real secrets manager — AWS SSM, HashiCorp Vault, Kubernetes
Secrets, Doppler, or your deployment platform's env-var UI — not from a
committed file. Pretending to scaffold a `.env.production` invites
placeholder credentials into version control.

The active file is selected via the `--env` flag:

```bash
# Use develop settings
fastman serve --env=develop

# Use staging settings
fastman serve --env=staging
```

When no `--env` flag is provided, Fastman auto-detects `.env.develop` if it
exists, otherwise falls back to `.env`.

### Production Configuration

In production, do **not** ship a `.env.production` file. Instead, inject
environment variables through your platform:

| Platform | Where to set vars |
|----------|-------------------|
| Docker / Compose | `environment:` section or `env_file:` pointing to a secrets-mounted file |
| Kubernetes | `Secret` + `envFrom:` in the pod spec |
| AWS ECS / Lambda | Task definition env or Secrets Manager |
| Fly.io | `fly secrets set` |
| Railway / Render / Vercel | Project settings UI |
| Bare metal / systemd | `EnvironmentFile=` directive |

The variables your app needs at boot are the same shape as `.env.staging`,
plus production-grade replacements:

```env
ENVIRONMENT=production
DEBUG=false
SECRET_KEY=<from-secrets-manager>

# Database
DB_HOST=<production-host>
DB_PORT=5432
DB_USER=<from-secrets-manager>
DB_PASSWORD=<from-secrets-manager>
DB_NAME=myapp

# CORS
ALLOWED_HOSTS=["https://myapp.com","https://www.myapp.com"]
```

Setting `ENVIRONMENT=production` causes `app/core/config.py` to look for
`.env.production`, fail to find it (correct!), and fall back to `.env` —
which itself should not exist on the production host, so the app reads
purely from injected env vars. That's the intended boot path.

### Generate a Secure Secret Key

```bash
fastman config:appkey --show
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
