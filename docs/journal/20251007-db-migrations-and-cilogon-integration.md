---
created: 2025-07-10
updated: 2025-07-16
author: Dan Tran
updated_by: Dan Tran
---

# AAO CILogon Integration

The following pull requests (https://github.com/ADMSCentre/australian-ad-observatory-api/pull/5) introduces two API endpoints to support CILogon integration:

* `/auth/cilogon/login` redirects to CILogon for authentication.
* `/auth/cilogon/callback` handles the callback from CILogon, retrieving the necessary user information and returning it in the response.

## Implementation Plan

Users currently get created with /users (POST) endpoint. It requires a username and a password. Users from CILogon won't have a username but they will have an email.

Consider:

* Remove the requirement for username and password (make them optional). Each user now has a unique ID.
* Add email as another optional field.
* Add another `user_identities` table with the following columns:
  * `user_id`: Foreign key to the `users` table.
  * `provider`: The identity provider (e.g., CILogon).
  * `provider_user_id`: The unique identifier for the user from the identity provider (e.g., CILogon ID).
  * `created_at`: Timestamp of when the identity was created.
* For current users, if they have a username, create a record in the `user_identities` table with the provider set to 'local' and the `provider_user_id` set to their username.
* By doing this, we can support both local users and SSO users (like CILogon) without changing the existing user management system.

The systems affected by this change include:

- The RDS PostgreSQL database
- The Lambda functions and multiple functions will be updated
- The front-end will also need to be updated to accommodate the new approach.

### Current Schema

```mermaid
erDiagram
  User {
    string id PK
    string username "Unique"
    string password "Hashed password"
    string full_name
    boolean enabled
    string role "admin, user"
    string current_token "JWT token"
  }
```

### Updated Schema

```mermaid
erDiagram
  User {
    string id PK
    string full_name "Optional"
    boolean enabled
    string role "admin, user"
  }
  UserIdentity {
    string user_id PK,FK
    string provider PK "local, cilogon"
    string provider_user_id
    string password "Optional"
    int created_at
  }
  User one to many UserIdentity: has
```

## Scope

Prior to the main task, we need to separate the production and development environments, including:

* A new `aao_v2_dev` database in the current RDS instance - this is where we will apply the migrations.
  * Will need to copy the current production database to the dev database.
* A new `fta-mobile-observations-api-dev` Lambda function that will use the dev database.

* Add a migration script to:
  * Create a user_identities table
  * Populate the user_identities table with local identities, using the username of current users as the provider_user_idand and move the password field from usersto user_identities
  * Remove the username and password fields from the users table
  * Should we stop storing JWT in the database? Yes, this breaks stateless design & it is not critical to disable "sessions" -> will need to update jwt.py to stop looking up current token
  * Update ad_attributes table's created_by and modified_by to reference the user_id instead of username

* Update JWT schema to include:
  * user_id (instead of username)
  * full_name
  * role
  * enabled

* Update API endpoints:
  * [POST] `users` should require (username, email, password) then 
    * create a new user in the users table as usual
    * insert into user_identities values (user_id, "local", username, password, current_timestamp)

* [GET] users should return a list of the following fields: (user_id, full_name, role, enabled) BREAKING CHANGE - WILL NEED TO UPDATE FRONT-END

* auth/cilogon/callback should select user_id from user_identities where provider = "cilogon" and provider_user_id = cilogon_client_id to check if a user already exists, and
  * if not found, create_new_cilogon_user(cilogon_client_id)
    * create a new user in the users table, then
    * insert into user_identities values (user_id, "cilogon", cilogon_client_id, current_timestamp)
    * return JWT generated from the new user

  * if found, select id, full_name, role, enabled from users where id = user_id and return the JWT generated from the matched user

* Update front end:
  * The user management table (at /users) should no longer show the username and password -> will need a different design to accommodate password editing for "local" authentication
  * 'local' vs CILogon sign-in: add CILogon interface but hide until alcohol study concludes

## Future Considerations

* Account linking - add an endpoint `auth/link_account` to allow users to link different identities to the same user(e.g., add a link to the self/edit endpoint to add CILogon identity to their account)
* [SELECTED FOR DEVELOPMENT] Email notification - should email be a field in users (like a primary email address) or user_identities (each identity provider may use a different email address), or a separate table user_email

## Execution

### [x] Setting up Alembic as the Migration Tool

Since we are using SQLAlchemy to interact with a PostgreSQL database (hosted as an RDS instance), we can use Alembic as the migration tool. [Alembic](https://alembic.sqlalchemy.org/en/latest/) is part of the SQLAlchemy project and can be used to manage database migrations.

**Step 1: Install Alembic**

Add Alembic to the project dependencies:

```bash
pip install alembic
```

Add `alembic` to `requirements.txt`:

```
alembic>=1.16.4
```

**Step 2: Initialize Alembic**

Initialize Alembic in the project root directory:

```bash
alembic init alembic
```

This creates:
- `alembic/` directory with migration scripts
- `alembic.ini` configuration file
- `alembic/env.py` environment configuration

**Step 3: Configure Alembic**

Since we'll be reading the database configuration from `config.ini` in the `env.py` file, we don't need a separate database URL in `alembic.ini`. Instead, we will set the database URL dynamically in `alembic/env.py`.

The actual database connection will be configured in `env.py` using the same `config.ini` file that the Lambda function uses.

**Step 4: Update env.py**

Modify `alembic/env.py` to import our SQLAlchemy models and configure the target metadata:

```python
# alembic/env.py
import os
import sys
from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool
from alembic import context
from configparser import ConfigParser
from models.base import Base

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

# Read database configuration from config.ini
config_parser = ConfigParser()
config_parser.read('config.ini')

DB_HOST = config_parser.get('POSTGRES', 'HOST')
DB_PORT = config_parser.get('POSTGRES', 'PORT')
DB_DATABASE = config_parser.get('POSTGRES', 'DATABASE')
DB_USERNAME = config_parser.get('POSTGRES', 'USERNAME')
DB_PASSWORD = config_parser.get('POSTGRES', 'PASSWORD')

db_url = f'postgresql://{DB_USERNAME}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_DATABASE}'

# this is the Alembic Config object
config = context.config

# Set up target metadata
target_metadata = Base.metadata

# Configure database URL from config.ini
config.set_main_option("sqlalchemy.url", db_url)
```

**Step 5: Create Initial Migration**

> [!NOTE]
>
> This step should be done if the database is empty, and it is intended to populate the database with the current state of the models. If the database already has data, there is no need to create an initial migration, as the existing data will be preserved.

Generate the initial migration based on current models.

```bash
alembic revision --autogenerate -m "Initial migration"
```

This will create a migration file in `alembic/versions/` that captures the current state of your database schema.

**Step 6: Run Migrations**

Apply migrations to the development database:

```bash
alembic upgrade head
```

This command applies all pending migrations to the database, updating its schema to match the current state of your models.

### [x] Update the Models

Before generating the migration script, we need to update the relevant models to support the new schema for CILogon integration.

**Changes made to `models/user.py`:**
- Created new `UserIdentityORM` model for the `user_identities` table with:
  - Composite primary key (`user_id`, `provider`)
  - Foreign key to `users.id`
  - Fields: `provider_user_id`, `password` (nullable), `created_at`
- Updated `UserORM` model:
  - Removed: `username`, `password`, `current_token` fields
  - Made `full_name` nullable for CILogon users
  - Added relationship to `user_identities`
- Created corresponding Pydantic models: `User` and `UserIdentity`

**Changes made to `models/attribute.py`:**
- Updated comments to clarify `created_by` and `modified_by` will reference `user.id` instead of username
- No structural changes (data migration handles the reference updates)

### [x] Generate Migration Script

The migration script handles both schema changes and data migration to ensure no data loss.

**Step 1: Generate Initial Migration**

```bash
alembic revision --autogenerate -m "Add user_identities table for sso"
```

**Step 2: Customize the Migration Script**

The auto-generated migration was customized to include:

**Upgrade process:**
- Create `user_identities` table with proper constraints
- Migrate existing user data to `user_identities` with provider='local'
- Update `ad_attributes` references from username to user_id
- Make `full_name` nullable
- Drop old columns (`username`, `password`, `current_token`)

**Downgrade process:**
- Restore old schema by re-adding dropped columns
- Migrate data back from `user_identities` to `users` (local users only)
- Restore constraints and references
- Drop `user_identities` table
- ⚠️ **Warning**: CILogon user data will be lost during downgrade

**Step 3: Test the Migration**

```bash
# Apply the migration
alembic upgrade head
```

**Verification checks:**
- `user_identities` table exists and is populated
- `users` table has correct schema  
- `ad_attributes` references are updated
- No data loss occurred

**Step 4: Verification Queries**

After migration, run these queries to verify the data migration was successful:

```sql
-- Check that all original users have local identities
SELECT COUNT(*) FROM users;
SELECT COUNT(*) FROM user_identities WHERE provider = 'local';
-- These counts should match

-- Check that ad_attributes references are valid user IDs
SELECT COUNT(*) FROM ad_attributes a 
LEFT JOIN users u ON a.created_by = u.id 
WHERE u.id IS NULL;
-- Should return 0

-- Check for any orphaned references
SELECT COUNT(*) FROM ad_attributes a 
LEFT JOIN users u ON a.modified_by = u.id 
WHERE u.id IS NULL;
-- Should return 0
```