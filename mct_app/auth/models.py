import datetime
from typing import Optional

from sqlalchemy import DateTime, Integer, String, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from mct_app import db

class User(db.Model):
    __tablename__ = "user"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    username: Mapped[str] = mapped_column(String(45), unique=True, nullable=False)
    password: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str] = mapped_column(String(120), unique=True, nullable=False)
    phone_number: Mapped[str] = mapped_column(String(12), unique=True)
    roles: Mapped[list['UserRole']] = relationship(back_populates="user")
    session_id: Mapped[int] = mapped_column(ForeignKey('session.id'))
    session: Mapped['Session'] = relationship()
    social_account_id: Mapped[int] = mapped_column(ForeignKey('social_account.id'))
    social_account: Mapped['SocialAccount'] = relationship(back_populates="users")

    def __repr__(self) -> str:
        return f"User(id={self.id!r}, name={self.username!r}"

class UserRole(db.Model):
    __tablename__ = 'user_role'
    user_id: Mapped[int] = mapped_column(ForeignKey('user.id'), primary_key=True)
    role_id: Mapped[int] = mapped_column(ForeignKey('role.id'), primary_key=True)
    
    role: Mapped['Role'] = relationship(back_populates='users')
    user: Mapped['User'] = relationship(back_populates='roles')

class Role(db.Model):
    __tablename__ = "role"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(80), unique=True, nullable=False)
    users: Mapped[list['UserRole']] = relationship(back_populates='role')
    permission_id: Mapped[int] = mapped_column(ForeignKey('permission.id'))
    permission: Mapped['Permission'] = relationship()

    def __repr__(self) -> str:
        return f"role={self.id!r}), name={self.name!r}"

class Session(db.Model):
    __tablename__ = 'session'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    ip_address: Mapped[str] = mapped_column(String(45))
    last_activity: Mapped[datetime] = mapped_column(DateTime)

class SocialAccount(db.Model):
    __tablename__ = 'social_account'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    driver: Mapped[str] = mapped_column(String(45))
    driver_id: Mapped[str] = mapped_column(String(45))
    avatar_url: Mapped[str] = mapped_column(String(255))
    users: Mapped[list['User']] = relationship(back_populates='social_account')

class Permission(db.Model):
    __tablename__ = 'permission'
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(45))
    description: Mapped[str] = mapped_column(String(255))