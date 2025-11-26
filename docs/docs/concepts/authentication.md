---
sidebar_position: 3
---

# Authentication

Security is hard. Fastman makes it easy with built-in scaffolding for modern authentication strategies.

## Supported Strategies

- **JWT (JSON Web Tokens)**: Standard stateless authentication.
- **Keycloak**: Integration with Keycloak Identity Provider.
- **OAuth2**: (Coming Soon)

## Scaffolding Auth

To add authentication to your project, simply run:

```bash
fastman install:auth --type=jwt
```

This command will:
1.  Install necessary dependencies (e.g., `pyjwt`, `passlib`).
2.  Generate `app/features/auth` with:
    - `router.py`: `/login`, `/register`, `/me` endpoints.
    - `service.py`: User creation and authentication logic.
    - `utils.py`: Password hashing and token generation.
3.  Create a `User` model.
4.  Create a migration file.

## Protecting Routes

Once installed, you can protect any route using the generated dependency:

```python
from app.features.auth.router import get_current_user

@router.get("/protected")
def protected_route(user = Depends(get_current_user)):
    return {"message": f"Hello, {user.email}"}
```
