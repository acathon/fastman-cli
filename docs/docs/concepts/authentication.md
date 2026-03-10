---
sidebar_position: 2
---

# Authentication

Fastman provides one-command authentication scaffolding for the most common auth patterns. Each generates production-ready code with proper security practices built in.

| Type | Best For | Command |
|------|----------|---------|
| **JWT** | Stateless APIs, mobile apps | `fastman install:auth --type=jwt` |
| **OAuth** | Social login (Google, GitHub, Discord) | `fastman install:auth --type=oauth --provider=google` |
| **Keycloak** | Enterprise SSO | `fastman install:auth --type=keycloak` |
| **Passkey** | Passwordless (biometric/hardware key) | `fastman install:auth --type=passkey` |

---

## JWT Authentication

The most common choice for stateless API authentication. Tokens are signed, self-contained, and require no server-side session storage.

```bash
fastman install:auth --type=jwt
```

This creates a complete auth feature module:

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

Auth variables are automatically added to all environment files (`.env.*`):

```env
SECRET_KEY=your-secret-key-here
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

Generate a secure secret key (updates all env files):

```bash
fastman generate:key
```

---

## OAuth Authentication

For "Login with Google/GitHub/etc." social login flows. Fully scaffolded with provider-specific configuration.

```bash
# Google (default)
fastman install:auth --type=oauth --provider=google

# GitHub
fastman install:auth --type=oauth --provider=github

# Discord
fastman install:auth --type=oauth --provider=discord
```

### Supported Providers

| Provider | Scopes | What You Get |
|----------|--------|--------------|
| **Google** | `openid email profile` | Email, name, avatar |
| **GitHub** | `read:user user:email` | Email, name, avatar |
| **Discord** | `identify email` | Email, username, avatar |

### Generated Files

```
app/features/auth/
├── oauth_config.py     # Provider configuration (authlib)
├── models.py           # User model with oauth_provider field
├── schemas.py          # UserRead, OAuthCallback schemas
├── service.py          # Create-or-update user from OAuth data
└── router.py           # /login, /callback, /me, /logout
```

### Generated Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/auth/login` | Redirect to OAuth provider |
| GET | `/auth/callback` | Handle provider callback |
| GET | `/auth/me` | Get current user |
| GET | `/auth/logout` | Clear session |

### Configuration

```env
OAUTH_CLIENT_ID=your-client-id
OAUTH_CLIENT_SECRET=your-client-secret
```

:::tip
Add `SessionMiddleware` to your `app/main.py` for OAuth session support:
```python
from starlette.middleware.sessions import SessionMiddleware
app.add_middleware(SessionMiddleware, secret_key=settings.SECRET_KEY)
```
:::

---

## Keycloak Authentication

Enterprise-grade identity and access management with single sign-on (SSO).

```bash
fastman install:auth --type=keycloak
```

This:
1. Installs `fastapi-keycloak-middleware`
2. Creates `app/core/keycloak.py`
3. Updates `app/core/config.py` with Keycloak settings
4. Adds environment variables to all `.env.*` files

### Configuration

```env
KEYCLOAK_URL=https://keycloak.example.com
KEYCLOAK_REALM=my-realm
KEYCLOAK_CLIENT_ID=my-client
KEYCLOAK_CLIENT_SECRET=your-secret
```

---

## Passkey Authentication (WebAuthn)

Passwordless authentication using biometrics, hardware keys, or device PINs. No passwords, no MFA — just tap your fingerprint or security key.

```bash
fastman install:auth --type=passkey
```

### How It Works

1. **Registration**: User's device creates a public/private key pair. The public key is stored on your server.
2. **Authentication**: The server sends a challenge, the device signs it with the private key, and the server verifies using the stored public key.

No password is ever created, stored, or transmitted.

### Generated Files

```
app/features/auth/
├── models.py           # User + PasskeyCredential models
├── schemas.py          # Registration/Authentication request schemas
├── service.py          # WebAuthn challenge generation & verification
├── security.py         # JWT session tokens (post-auth)
├── dependencies.py     # get_current_user dependency
└── router.py           # Registration & authentication endpoints
```

### Generated Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/auth/passkey/register/options` | Get registration challenge |
| POST | `/auth/passkey/register/verify` | Store new passkey |
| POST | `/auth/passkey/authenticate/options` | Get login challenge |
| POST | `/auth/passkey/authenticate/verify` | Verify & get token |
| GET | `/auth/passkey/me` | Current user info |
| GET | `/auth/passkey/credentials` | List registered passkeys |
| DELETE | `/auth/passkey/credentials/{id}` | Remove a passkey |

### Configuration

```env
PASSKEY_RP_ID=localhost
PASSKEY_RP_NAME=My App
PASSKEY_ORIGIN=http://localhost:8000
```

In production, set `PASSKEY_RP_ID` to your domain (e.g. `example.com`) and `PASSKEY_ORIGIN` to `https://example.com`.

### Frontend Integration

The backend provides the WebAuthn options and verification. You'll need a small JavaScript client to interact with the browser's `navigator.credentials` API:

```javascript
// Registration
const options = await fetch('/auth/passkey/register/options', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ email: 'user@example.com', username: 'user' })
}).then(r => r.json());

const credential = await navigator.credentials.create({ publicKey: options });

await fetch('/auth/passkey/register/verify', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ email: 'user@example.com', credential })
});
```

:::tip Why Passkeys?
Passkeys eliminate passwords entirely. No password reuse, no phishing, no MFA fatigue. A single biometric scan or hardware tap replaces passwords + SMS codes + authenticator apps.
:::

---

## Best Practices

1. **Always use HTTPS** in production
2. **Store secrets in environment variables**, never in code
3. **Use short-lived tokens** (15-30 minutes for JWT, 60 minutes for passkey sessions)
4. **Implement refresh tokens** for long sessions
5. **Hash passwords** with bcrypt (Fastman does this automatically for JWT)
6. **Prefer passkeys** for new projects — they're more secure and easier for users
