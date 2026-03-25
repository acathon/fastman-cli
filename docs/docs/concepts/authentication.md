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
fastman config:appkey
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

Enterprise-grade identity and access management with single sign-on (SSO). Powered by [`fastapi-keycloak`](https://github.com/fastapi-keycloak/fastapi-keycloak).

```bash
fastman install:auth --type=keycloak
```

If your Keycloak instance or upstream gateway uses a private CA, append your project certificates during setup:

```bash
fastman install:auth --type=keycloak --append-certificate
```

This:
1. Installs `fastapi-keycloak`
2. Creates `app/core/keycloak.py` with a `FastAPIKeycloak` instance and Swagger OAuth config
3. Registers a `GET /me` endpoint that returns the current authenticated user
4. Updates `app/core/config.py` with Keycloak settings
5. Adds environment variables to all `.env.*` files
6. Optionally appends certificates from `certs/` to the local `certifi` bundle

### Generated Endpoint

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/me` | Return the current authenticated Keycloak user |

### Configuration

```env
KEYCLOAK_URL=https://keycloak.example.com
KEYCLOAK_REALM=my-realm
KEYCLOAK_CLIENT_ID=my-client
KEYCLOAK_CLIENT_SECRET=your-secret
KEYCLOAK_ADMIN_SECRET=your-admin-cli-secret
KEYCLOAK_CALLBACK_URI=http://localhost:8000/callback
KEYCLOAK_VERIFY_SSL=true
```

| Variable | Description | Default |
|----------|-------------|---------|
| `KEYCLOAK_URL` | Keycloak server URL (with `/auth` suffix if required by your version) | `http://localhost:8080` |
| `KEYCLOAK_REALM` | Keycloak realm name | `master` |
| `KEYCLOAK_CLIENT_ID` | Client ID for your application | — |
| `KEYCLOAK_CLIENT_SECRET` | Client secret | — |
| `KEYCLOAK_ADMIN_SECRET` | Secret for the `admin-cli` client (required for user/role management) | — |
| `KEYCLOAK_CALLBACK_URI` | OAuth2 callback URL — must match a Valid Redirect URI in Keycloak | `http://localhost:8000/callback` |
| `KEYCLOAK_VERIFY_SSL` | `true` — enable SSL verification; `false` — disable (not recommended for production) | `true` |

### Protecting Routes

Unlike middleware-based approaches, `fastapi-keycloak` uses **dependency injection**. Routes are unprotected by default — you opt in per-route:

```python
from fastapi import Depends
from fastapi_keycloak import OIDCUser
from app.core.keycloak import get_current_user

@router.get("/protected")
def protected_route(user: OIDCUser = Depends(get_current_user)):
    return {"message": f"Hello, {user.email}"}
```

To require specific roles:

```python
from app.core.keycloak import idp

get_admin = idp.get_current_user(required_roles=["admin"])

@router.get("/admin")
def admin_route(user: OIDCUser = Depends(get_admin)):
    return {"message": f"Welcome admin {user.email}"}
```

### Swagger Authorize Button

`init_keycloak(app)` calls `idp.add_swagger_config(app)` and registers the `/me` endpoint. The Swagger UI automatically gets an **Authorize** button — click it to authenticate with Keycloak before testing protected endpoints.

### Private CA / Certificate Support

For environments that terminate TLS with an internal CA, store your certificate chain in the project-level `certs/` directory using `.pem` or `.crt` files.

```text
your-project/
├── app/
├── certs/
│   └── company-root-chain.pem
└── pyproject.toml
```

Example for a Keycloak deployment behind an internal gateway:

```text
certs/
├── keycloak-root-ca.pem
└── company-intermediate-ca.crt
```

If `KEYCLOAK_URL=https://sso.internal.example.com`, place the CA chain that signs that endpoint in `certs/` before running the install command.

You can append those certificates in two ways:

```bash
# During Keycloak installation
fastman install:auth --type=keycloak --append-certificate

# Or later as a standalone step
fastman install:certificate
```

Fastman creates a backup of the original `certifi` CA bundle before appending new certificates and skips certificates that are already present.

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
