"""add_user_roles_and_admin_portal_schema

Revision ID: f6a91c8230b1
Revises: 6c8ca07763d0
Create Date: 2026-11-16 02:15:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "f6a91c8230b1"
down_revision: Union[str, None] = "6c8ca07763d0"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Update users table using SQLite-compatible batch operations
    with op.batch_alter_table("users", schema=None) as batch_op:
        batch_op.add_column(
            sa.Column("role", sa.String(length=20), server_default="USER", nullable=False)
        )
        batch_op.add_column(
            sa.Column("is_active", sa.Boolean(), server_default=sa.true(), nullable=False)
        )
        batch_op.add_column(
            sa.Column("must_change_password", sa.Boolean(), server_default=sa.false(), nullable=False)
        )
        batch_op.create_index("ix_users_role", ["role"])
        batch_op.create_index("ix_users_is_active", ["is_active"])

    # 2. Create system_settings table for platform-wide administrative controls
    op.create_table(
        "system_settings",
        sa.Column("key", sa.String(length=50), primary_key=True),
        sa.Column("value", sa.String(length=255), nullable=False),
        sa.Column("description", sa.String(length=255), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )

    # 3. Insert default settings
    op.execute(
        "INSERT INTO system_settings (key, value, description) "
        "VALUES ('registration_enabled', 'true', 'Whether public user registration is permitted')"
    )


def downgrade() -> None:
    op.drop_table("system_settings")
    with op.batch_alter_table("users", schema=None) as batch_op:
        batch_op.drop_index("ix_users_is_active")
        batch_op.drop_index("ix_users_role")
        batch_op.drop_column("must_change_password")
        batch_op.drop_column("is_active")
        batch_op.drop_column("role")
