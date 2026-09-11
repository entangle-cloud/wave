from typing import Union

from collections.abc import Sequence
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = "60d893536494"
down_revision: Union[str, Sequence[str], None] = "078debe32354"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create shares table."""

    # Explicitly define the Postgres ENUM type
    share_role = postgresql.ENUM(
        "VIEWER",
        "EDITOR",
        "ADMIN",
        name="share_role",
        create_type=False,  # Prevents auto-creation inside op.create_table
    )

    # Manually create the enum safely first
    share_role.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "shares",
        sa.Column(
            "id",
            sa.Integer(),
            primary_key=True,
            nullable=False,
        ),
        sa.Column(
            "category_id",
            sa.Integer(),
            nullable=False,
        ),
        sa.Column(
            "user_id",
            sa.Integer(),
            nullable=False,
        ),
        sa.Column(
            "granted_by_id",
            sa.Integer(),
            nullable=True,
        ),
        sa.Column(
            "role",
            share_role,
            nullable=False,
            server_default="VIEWER",
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.ForeignKeyConstraint(
            ["category_id"],
            ["categories.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["granted_by_id"],
            ["users.id"],
            ondelete="SET NULL",
        ),
        sa.UniqueConstraint(
            "category_id",
            "user_id",
            name="uq_category_user_share",
        ),
    )


def downgrade() -> None:
    """Drop shares table."""

    op.drop_table("shares")

    share_role = postgresql.ENUM(
        "VIEWER",
        "EDITOR",
        "ADMIN",
        name="share_role",
    )

    share_role.drop(op.get_bind(), checkfirst=True)