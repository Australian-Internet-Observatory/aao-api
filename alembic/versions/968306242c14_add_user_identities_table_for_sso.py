"""Add user_identities table for sso

Revision ID: 968306242c14
Revises: 
Create Date: 2025-07-16 15:16:06.473981

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import text
import time


# revision identifiers, used by Alembic.
revision: str = '968306242c14'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Step 1: Create user_identities table
    op.create_table('user_identities',
    sa.Column('user_id', sa.VARCHAR(), nullable=False),
    sa.Column('provider', sa.VARCHAR(), nullable=False),
    sa.Column('provider_user_id', sa.VARCHAR(), nullable=False),
    sa.Column('password', sa.VARCHAR(), nullable=True),
    sa.Column('created_at', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
    sa.PrimaryKeyConstraint('user_id', 'provider')
    )
    
    # Step 2: Migrate existing user data to user_identities
    # Get current timestamp
    current_timestamp = int(time.time())
    
    # Insert local identities for existing users
    connection = op.get_bind()
    connection.execute(text("""
        INSERT INTO user_identities (user_id, provider, provider_user_id, password, created_at)
        SELECT id, 'local', username, password, :timestamp
        FROM users
        WHERE username IS NOT NULL
    """), {'timestamp': current_timestamp})
    
    # Step 3: Update ad_attributes references from username to user_id
    # Update created_by field
    connection.execute(text("""
        UPDATE ad_attributes 
        SET created_by = users.id
        FROM users 
        WHERE ad_attributes.created_by = users.username
    """))
    
    # Update modified_by field
    connection.execute(text("""
        UPDATE ad_attributes 
        SET modified_by = users.id
        FROM users 
        WHERE ad_attributes.modified_by = users.username
    """))
    
    # Step 4: Make full_name nullable
    op.alter_column('users', 'full_name',
               existing_type=sa.VARCHAR(),
               nullable=True)
    
    # Step 5: Drop old columns from users table
    op.drop_constraint(op.f('users_username_key'), 'users', type_='unique')
    op.drop_column('users', 'current_token')  # Remove JWT storage for stateless design
    op.drop_column('users', 'password')
    op.drop_column('users', 'username')


def downgrade() -> None:
    """Downgrade schema."""
    # WARNING: This downgrade will result in data loss for CILogon users
    
    # Step 1: Re-add dropped columns to users table
    op.add_column('users', sa.Column('username', sa.VARCHAR(), autoincrement=False, nullable=True))
    op.add_column('users', sa.Column('password', sa.VARCHAR(), autoincrement=False, nullable=True))
    op.add_column('users', sa.Column('current_token', sa.VARCHAR(), autoincrement=False, nullable=True))
    
    # Step 2: Restore username and password from user_identities for local users
    connection = op.get_bind()
    connection.execute(text("""
        UPDATE users 
        SET username = ui.provider_user_id, password = ui.password
        FROM user_identities ui
        WHERE users.id = ui.user_id AND ui.provider = 'local'
    """))
    
    # Step 3: Make username and password non-nullable and unique
    op.alter_column('users', 'username', nullable=False)
    op.alter_column('users', 'password', nullable=False)
    op.alter_column('users', 'full_name', existing_type=sa.VARCHAR(), nullable=False)
    op.create_unique_constraint(op.f('users_username_key'), 'users', ['username'], postgresql_nulls_not_distinct=False)
    
    # Step 4: Restore ad_attributes references from user_id back to username
    connection.execute(text("""
        UPDATE ad_attributes 
        SET created_by = users.username
        FROM users 
        WHERE ad_attributes.created_by = users.id
    """))
    
    connection.execute(text("""
        UPDATE ad_attributes 
        SET modified_by = users.username
        FROM users 
        WHERE ad_attributes.modified_by = users.id
    """))
    
    # Step 5: Drop user_identities table
    op.drop_table('user_identities')
