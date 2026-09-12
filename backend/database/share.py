import enum
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database.base import Base
from database.category import Category
from database.user import User


class ShareRole(str, enum.Enum):
    VIEWER = "viewer"
    EDITOR = "editor"
    ADMIN = "admin"


class Share(Base):
    __tablename__ = "shares"

    id: Mapped[int] = mapped_column(primary_key=True)

    category_id: Mapped[int] = mapped_column(
        ForeignKey("categories.id", ondelete="CASCADE"),
        nullable=False,
    )

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )

    granted_by_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )

    role: Mapped[ShareRole] = mapped_column(
        Enum(
            ShareRole,
            name="share_role",
            native_enum=True,
        ),
        default=ShareRole.VIEWER,
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    category: Mapped["Category"] = relationship()

    user: Mapped["User"] = relationship(
        foreign_keys=[user_id],
    )

    granted_by: Mapped["User | None"] = relationship(
        foreign_keys=[granted_by_id],
    )

    __table_args__ = (
        UniqueConstraint(
            "category_id",
            "user_id",
            name="uq_category_user_share",
        ),
    )
