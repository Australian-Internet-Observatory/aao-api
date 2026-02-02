# Authentication Middleware

This document describes the authentication system used in the Australian Ad Observatory API, including the JWT-based authentication mechanism and how it integrates with the middleware framework.

## Overview

The API uses JSON Web Tokens (JWT) for authentication. When a user logs in successfully, they receive a JWT that must be included in subsequent requests to access protected endpoints. The authentication middleware validates this token and attaches user information to the request.

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

## OpenAPI Documentation

The authenticate middleware automatically injects the following security requirement into the generated OpenAPI documentation:

```yaml
security:
  - bearerAuth: []
```

The security scheme is defined in the components section of the API specification:

```yaml
components:
  securitySchemes:
    bearerAuth:
      type: http
      scheme: bearer
      bearerFormat: JWT
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
