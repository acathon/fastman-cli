---
sidebar_position: 2
---

# Authentication

Fastman provides one-command authentication scaffolding for common auth patterns.

## JWT Authentication

The most common choice for API authentication.

```bash
fastman install:auth jwt
```

This creates:

```
app/features/auth/
├── __init__.py
├── models.py           # User model with password hashing
├── schemas.py          # Login, Register, Token schemas
├── security.py         # JWT token creation/verification
├── service.py          # Auth business logic
├── dependencies.py     # get_current_user dependency
└── router.py           # /register, /login, /me endpoints
```

### Generated Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/auth/register` | Create new user |
| POST | `/auth/login` | Get access token |
| GET | `/auth/me` | Get current user |

### Usage Example

```python
from app.features.auth.dependencies import get_current_user
from app.features.auth.models import User

@router.get("/protected")
def protected_route(user: User = Depends(get_current_user)):
    return {"message": f"Hello, {user.email}"}
```

### Configuration

Add to your `.env`:

```env
SECRET_KEY=your-secret-key-here
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

Generate a secure secret key:

```bash
fastman generate:key
```

---

## OAuth Authentication

For "Login with Google/GitHub" flows.

```bash
fastman install:auth oauth
```

Installs `authlib` and `httpx`. Requires manual configuration for your OAuth provider.

---

## Keycloak Authentication

Enterprise-grade identity management.

```bash
fastman install:auth keycloak
```

This:
1. Installs `fastapi-keycloak-middleware`
2. Creates `app/core/keycloak.py`
3. Updates `app/core/config.py` with Keycloak settings
4. Adds environment variables to `.env`

### Configuration

```env
KEYCLOAK_URL=https://keycloak.example.com
KEYCLOAK_REALM=my-realm
KEYCLOAK_CLIENT_ID=my-client
KEYCLOAK_CLIENT_SECRET=your-secret
```

---

## Best Practices

1. **Always use HTTPS** in production
2. **Store secrets in environment variables**, never in code
3. **Use short-lived tokens** (15-30 minutes)
4. **Implement refresh tokens** for long sessions
5. **Hash passwords** with bcrypt (Fastman does this automatically)
