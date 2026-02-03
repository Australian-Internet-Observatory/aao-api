# Authentication Middleware

This document describes the authentication system used in the Australian Ad Observatory API, including both JWT-based authentication for user sessions and API key authentication for programmatic access.

## Overview

The API supports two complementary authentication methods:

1. **JWT (JSON Web Tokens)**: For user login flows and web applications. JWTs are time-limited tokens (default 24-hour expiration) that require re-authentication when expired.
2. **API Keys**: For programmatic access, scripts, and automation. API keys are long-lived credentials that do not expire but can be revoked by deletion.

The authentication middleware validates both authentication methods and populates user information in the request context.

## API Key Authentication

API keys provide a simple alternative to JWTs for programmatic access and automation scenarios.

### Key Characteristics

| Aspect | JWT | API Key |
| ------ | --- | ------- |
| **Purpose** | User login, web sessions | Scripts, automation, CI/CD |
| **Expiration** | Yes (default 24h) | No (revoke-only) |
| **Format** | 3-part token (header.payload.signature) | 64-character opaque string |
| **Header** | `Authorization: Bearer <token>` | `X-API-Key: <key>` |
| **Creation** | Automatic on login | Manual via `/api-keys` endpoint |
| **Management** | Automatic expiration | Manual deletion to revoke |

### Creating and Using API Keys

**Step 1: Create an API Key** (requires JWT authentication)

```bash
curl -X POST https://api.example.com/api-keys \
  -H "Authorization: Bearer <jwt_token>" \
  -H "Content-Type: application/json" \
  -d '{"title": "My Script", "description": "Automated data export"}'
```

Response (key shown only once):
```json
{
  "api_key": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "title": "My Script",
    "key": "k8f3j2h5g9m1n4p7q0r6s8t2u5v9w3x1y7z8a9b0c1d2e3f4g5h6i7j8k9l0mnopqr",
    "suffix": "mnopqr",
    "created_at": "2026-02-02T10:30:00Z"
  }
}
```

**Step 2: Use the API Key**

```bash
curl https://api.example.com/data \
  -H "X-API-Key: k8f3j2h5g9m1n4p7q0r6s8t2u5v9w3x1y7z8a9b0c1d2e3f4g5h6i7j8k9l0mnopqr"
```

### Security Best Practices

- **Store Securely**: Keep API keys in environment variables, secrets managers, or secure configuration files
- **Never Commit**: Do not commit keys to version control
- **Rotate Regularly**: Revoke and recreate keys periodically for long-lived integrations
- **Revoke Immediately**: Delete keys if they are compromised
- **Use Appropriate Permissions**: Currently, keys inherit the full permissions of their owner user

### Visibility in List Responses

When listing API keys via `GET /api-keys`, only the last 6 characters (suffix) are shown, never the full key:

```json
{
  "api_keys": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "title": "My Script",
      "suffix": "mnopqr",
      "created_at": "2026-02-02T10:30:00Z",
      "last_used_at": "2026-02-02T14:45:00Z"
    }
  ]
}
```

## JWT Token Structure

The JWT follows a standard structure with three parts separated by dots: `{header}.{payload}.{signature}`

### Header
```json
{
  "alg": "HS256",
  "typ": "JWT"
}
```

### Payload
The token payload contains the following claims:

| Field       | Type           | Description                                                  |
| ----------- | -------------- | ------------------------------------------------------------ |
| `sub`       | string         | Subject identifier (user ID)                                 |
| `iat`       | int            | Issued at timestamp (Unix epoch)                             |
| `exp`       | int            | Expiration timestamp (Unix epoch)                            |
| `role`      | string         | User role (`guest`, `user`, `admin`)                         |
| `full_name` | string         | User's full name                                             |
| `enabled`   | boolean        | Whether the user account is enabled                          |
| `provider`  | string \| null | Identity provider (`local`, `cilogon`, or `null` for guests) |

### Signature
The signature is generated using HMAC-SHA256 with the secret key defined in `config.jwt.secret`:
```
SHA256(base64(header) + "." + base64(payload) + "." + JWT_SECRET)
```

## Authentication Flow

### Login Flow

1. **Local Authentication** (`POST /auth/login`):
   - User submits `username` and `password`
   - System looks up the user identity in `user_identities` table where `provider='local'`
   - Password is hashed using MD5 and compared with stored hash
   - On success, a JWT is created and returned

2. **CILogon Authentication** (`GET /auth/cilogon/login`):
   - Initiates OAuth 2.0 flow with CILogon
   - User authenticates through their institution
   - On callback, system maps the external identity to a local user
   - JWT is created and returned

### Token Verification Flow

```
Request with Authorization: Bearer {token}
           │
           ▼
┌──────────────────────────┐
│  Check headers exist     │──No──▶ 401 NO_HEADERS
└──────────────────────────┘
           │Yes
           ▼
┌──────────────────────────┐
│  Check Authorization     │──No──▶ 401 NO_AUTHORIZATION_HEADER
│  header exists           │
└──────────────────────────┘
           │Yes
           ▼
┌──────────────────────────┐
│  Check "Bearer " prefix  │──No──▶ 401 INVALID_AUTHORIZATION_HEADER
└──────────────────────────┘
           │Yes
           ▼
┌──────────────────────────┐
│  Verify token signature  │──No──▶ 401 SESSION_TOKEN_EXPIRED
│  and expiration          │
└──────────────────────────┘
           │Yes
           ▼
┌──────────────────────────┐
│  Check if guest role     │──Yes─▶ Set event['user'] and continue
└──────────────────────────┘
           │No
           ▼
┌──────────────────────────┐
│  Check user exists in DB │──No──▶ 401 USER_NOT_FOUND
└──────────────────────────┘
           │Yes
           ▼
    Set event['user'] and event['identity']
    Continue to route handler
```

## Middleware Implementation

### The `authenticate` Middleware

Location: [middlewares/authenticate.py](../../middlewares/authenticate.py)

The authenticate middleware:
1. Extracts the JWT from the `Authorization: Bearer {token}` header
2. Verifies the token signature and expiration
3. Retrieves the user from the database (for non-guest tokens)
4. Attaches user information to the event object

**Event Properties Set:**
- `event['user']`: A `User` object containing:
  - `id`: User's unique identifier (UUID)
  - `full_name`: User's display name
  - `enabled`: Account status
  - `role`: User role (`guest`, `user`, `admin`)
  - `primary_email`: User's email address (if available)
- `event['identity']`: A `UserIdentity` object containing:
  - `user_id`: Reference to the user
  - `provider`: Identity provider (`local`, `cilogon`)
  - `provider_user_id`: Username or external ID
  - `created_at`: Identity creation timestamp

### The `authorise` Middleware

Location: [middlewares/authorise.py](../../middlewares/authorise.py)

The authorise middleware enforces role-based access control. It must be used **after** the authenticate middleware.

```python
from middlewares.authenticate import authenticate
from middlewares.authorise import Role, authorise
from utils import use

@route('/admin-only', 'GET')
@use(authenticate)
@use(authorise(Role.ADMIN))
def admin_endpoint(event, response, context):
    # Only accessible by admin users
    pass
```

**Available Roles:**
- `Role.GUEST`: Temporary, unauthenticated users (system-generated)
- `Role.USER`: Standard authenticated users
- `Role.ADMIN`: Administrators with full access

**Error Responses:**
- `401 MUST_USE_AFTER_AUTHENTICATE`: authorise used without authenticate
- `403 USER_NOT_ENABLED`: User account is disabled
- `403 Must be one of the following roles: ...`: Role check failed

## Usage Examples

### Basic Protected Endpoint

```python
from routes import route
from middlewares.authenticate import authenticate
from utils import use, Response

@route('/protected', 'GET')
@use(authenticate)
def protected_endpoint(event, response: Response, context):
    """Access user information from the authenticated request.
    ---
    responses:
      200:
        description: Success
    """
    user = event['user']
    return {
        "message": f"Hello, {user.full_name}!",
        "user_id": user.id,
        "role": user.role
    }
```

### Role-Restricted Endpoint

```python
from routes import route
from middlewares.authenticate import authenticate
from middlewares.authorise import Role, authorise
from utils import use, Response

@route('/admin/users', 'GET')
@use(authenticate)
@use(authorise(Role.ADMIN))
def list_all_users(event, response: Response, context):
    """Admin-only endpoint.
    ---
    responses:
      200:
        description: List of users
      403:
        description: Forbidden - Admin role required
    """
    # Only admins can reach this code
    pass
```

### Multiple Allowed Roles

```python
@route('/data', 'GET')
@use(authenticate)
@use(authorise(Role.USER, Role.ADMIN))
def get_data(event, response: Response, context):
    """Accessible by both users and admins."""
    pass
```

### Using API Key Authentication

API keys can be used to authenticate requests without a JWT:

```bash
# Create an API key (requires JWT authentication)
curl -X POST \
  -H "Authorization: Bearer <jwt_token>" \
  -H "Content-Type: application/json" \
  -d '{"title": "Data Export Script"}' \
  https://api.example.com/api-keys

# Response (note: key shown only once):
# {
#   "api_key": {
#     "id": "550e8400-e29b-41d4-a716-446655440000",
#     "title": "Data Export Script",
#     "key": "k8f3j2h5g9m1n4p7q0r6s8t2u5v9w3x1y7z8a9b0c1d2e3f4g5h6i7j8k9l0mnopqr",
#     "suffix": "mnopqr",
#     "created_at": "2026-02-02T10:30:00Z"
#   }
# }

# Use the API key to access endpoints
curl -H "X-API-Key: k8f3j2h5g9m1n4p7q0r6s8t2u5v9w3x1y7z8a9b0c1d2e3f4g5h6i7j8k9l0mnopqr" \
  https://api.example.com/data

# List API keys
curl -H "X-API-Key: <api_key>" \
  https://api.example.com/api-keys

# Revoke an API key
curl -X DELETE \
  -H "X-API-Key: <api_key>" \
  https://api.example.com/api-keys/550e8400-e29b-41d4-a716-446655440000
```

Note: **API keys cannot be used to create or manage themselves**. You must use a JWT token to create new API keys. Once created, the API key can be used for data access and listing/revoking its own key.

## OpenAPI Documentation

The authenticate middleware automatically injects the following security requirement into the generated OpenAPI documentation:

```yaml
security:
  - bearerAuth: []
  - apiKeyAuth: []
```

The security schemes are defined in the components section of the API specification:

```yaml
components:
  securitySchemes:
    bearerAuth:
      type: http
      scheme: bearer
      bearerFormat: JWT
    apiKeyAuth:
      type: apiKey
      in: header
      name: X-API-Key
      description: API key for programmatic access (non-expiring)
```

## JWT Utility Functions

Location: [utils/jwt.py](../../utils/jwt.py)

### Key Functions

| Function                                   | Description                                   |
| ------------------------------------------ | --------------------------------------------- |
| `create_token(user, provider, expire)`     | Create a JWT for a user                       |
| `create_session_token(username, password)` | Authenticate and create token for local users |
| `create_guest_token()`                     | Create a token for guest access               |
| `verify_token(token)`                      | Verify token signature and expiration         |
| `decode_token(token)`                      | Decode and return token payload               |

### JsonWebToken Class

The `JsonWebToken` dataclass provides an object-oriented interface for working with tokens:

```python
from utils import jwt

# Create token from user
token_obj = jwt.JsonWebToken.from_user(user, provider='local')
token_string = token_obj.token

# Decode token
token_obj = jwt.JsonWebToken.from_token(token_string)
user = token_obj.user  # Retrieves User from database
identity = token_obj.identity  # Retrieves UserIdentity from database
```

## Database Models

### Users Table

| Column          | Type      | Description             |
| --------------- | --------- | ----------------------- |
| `id`            | UUID (PK) | Unique user identifier  |
| `full_name`     | string    | User's display name     |
| `enabled`       | boolean   | Account status          |
| `role`          | string    | User role               |
| `primary_email` | string    | User's email (optional) |

### User Identities Table

Supports multiple authentication providers per user.

| Column             | Type          | Description                            |
| ------------------ | ------------- | -------------------------------------- |
| `user_id`          | UUID (FK, PK) | Reference to users table               |
| `provider`         | string (PK)   | Identity provider (`local`, `cilogon`) |
| `provider_user_id` | string        | Username or external identifier        |
| `password`         | string        | Hashed password (local provider only)  |
| `created_at`       | int           | Creation timestamp                     |

## Configuration

JWT settings are configured in the application configuration file:

```ini
[JWT]
SECRET = your-secret-key
EXPIRATION = 86400  # Token expiration in seconds (default: 24 hours)
```

## Error Codes Reference

| Code                           | HTTP Status | Description                                       |
| ------------------------------ | ----------- | ------------------------------------------------- |
| `NO_HEADERS`                   | 401         | Request has no headers                            |
| `NO_AUTHORIZATION_HEADER`      | 401         | Missing Authorization header                      |
| `INVALID_AUTHORIZATION_HEADER` | 401         | Authorization header doesn't start with "Bearer " |
| `SESSION_TOKEN_EXPIRED`        | 401         | Token signature invalid or token expired          |
| `USER_NOT_FOUND`               | 401         | User in token doesn't exist in database           |
| `MUST_USE_AFTER_AUTHENTICATE`  | 401         | authorise middleware used without authenticate    |
| `USER_NOT_ENABLED`             | 403         | User account is disabled                          |
| `INVALID_CREDENTIALS`          | 400         | Invalid username or password (login)              |
