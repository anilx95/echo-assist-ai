"""Add hashed one-time account action tokens.

Revision ID: 20261107_03
Revises: 20261107_02
"""

from alembic import op
import sqlalchemy as sa


revision = "20261107_03"
down_revision = "20261107_02"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    existing_tables = set(inspector.get_table_names())

    if "account_tokens" not in existing_tables:
        op.create_table(
            "account_tokens",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
            sa.Column("token_hash", sa.String(length=64), nullable=False),
            sa.Column("purpose", sa.String(length=40), nullable=False),
            sa.Column("expires_at", sa.DateTime(), nullable=False),
            sa.Column("used_at", sa.DateTime(), nullable=True),
            sa.Column("created_at", sa.DateTime(), nullable=False),
        )
        op.create_index("ix_account_tokens_user_id", "account_tokens", ["user_id"])
        op.create_index("ix_account_tokens_token_hash", "account_tokens", ["token_hash"], unique=True)
        op.create_index("ix_account_tokens_purpose", "account_tokens", ["purpose"])


def downgrade() -> None:
    op.drop_table("account_tokens")
