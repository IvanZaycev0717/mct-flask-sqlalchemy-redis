from sqlalchemy import Integer, String, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from mct_app import db

class User(db.Model):
    __tablename__ = "user_account"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    username: Mapped[str] = mapped_column(String(80), unique=True, nullable=False)
    email: Mapped[str] = mapped_column(String(120), unique=True, nullable=False)
    password: Mapped[str] = mapped_column(String(255), nullable=False)
    role_id: Mapped[int] = mapped_column(Integer, ForeignKey('role.id'), nullable=False)
    roles: Mapped[list['Role']] = relationship(back_populates='user')

    def __repr__(self) -> str:
        return f"User(id={self.id!r}, name={self.username!r}, role={self.role_id!r})"

class Role(db.Model):
    __tablename__ = "role"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(80), unique=True, nullable=False)
    user: Mapped[User] = relationship(back_populates="roles")

    def __repr__(self) -> str:
        return f"role={self.id!r}), name={self.name!r}"

