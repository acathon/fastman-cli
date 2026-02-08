---
sidebar_position: 10
---

# Deployment

Overview of deployment strategies for Fastman applications.

## Quick Deploy Options

| Platform | Difficulty | Best For |
|----------|------------|----------|
| [Railway](https://railway.app) | Easy | Quick deploys, free tier |
| [Render](https://render.com) | Easy | Full-stack apps |
| [Fly.io](https://fly.io) | Medium | Edge deployment |
| [AWS ECS](https://aws.amazon.com) | Advanced | Enterprise scale |
| [DigitalOcean](https://digitalocean.com) | Medium | VPS control |

## Environment Setup

### Production .env

```env
# Core
DEBUG=false
SECRET_KEY=your-production-secret-here

# Database
DATABASE_URL=postgresql://user:pass@host:5432/db

# Optional
CORS_ORIGINS=https://myapp.com,https://www.myapp.com
```

### Generate Secret Key

```bash
fastman generate:key
```

## Health Checks

Add a health endpoint for container orchestration:

```python
# app/main.py
@app.get("/health")
def health_check():
    return {"status": "healthy"}
```

## Next Steps

See the [Production Build](/advanced/production-build) guide for detailed Docker and optimization instructions.
