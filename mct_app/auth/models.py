import csv
import datetime
from typing import List, Optional
import os

from sqlalchemy import DateTime, Integer, String, ForeignKey, select
from sqlalchemy.orm import Mapped, mapped_column, relationship
from werkzeug.security import check_password_hash, generate_password_hash
from flask_login import UserMixin

from mct_app import db, login_manager

class User(UserMixin, db.Model):
    __tablename__ = "user"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    username: Mapped[str] = mapped_column(String(45), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str] = mapped_column(String(120), unique=True, nullable=False)
    phone: Mapped[str] = mapped_column(String(12), unique=True, nullable=True)
    session_id: Mapped[int] = mapped_column(ForeignKey('session.id'), nullable=True)
    social_account_id: Mapped[int] = mapped_column(ForeignKey('social_account.id'), nullable=True)

    roles: Mapped[List['UserRole']] = relationship(back_populates="user")
    user_session: Mapped['UserSession'] = relationship()
    social_account: Mapped['SocialAccount'] = relationship(back_populates="users")

    @property
    def password(self):
        raise AttributeError('Пароль не должен быть получен')

    @password.setter
    def password(self, password):
        self.password_hash = generate_password_hash(password)

    def verify_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def create_admin():
        if not User.query.filter_by(username=os.environ.get('ADMIN_NAME')).first():
            admin = User(
                username=os.environ.get('ADMIN_NAME'),
                password=os.environ.get('ADMIN_PASS'),
                email=os.environ.get('ADMIN_EMAIL'))
            db.session.add(admin)
            db.session.commit()


class UserRole(db.Model):
    __tablename__ = 'user_role'
    user_id: Mapped[int] = mapped_column(ForeignKey('user.id'), primary_key=True)
    role_id: Mapped[int] = mapped_column(ForeignKey('role.id'), primary_key=True)
    
    role: Mapped['Role'] = relationship(back_populates='users')
    user: Mapped['User'] = relationship(back_populates='roles')

    def create_admin_role():
        if not UserRole.query.filter_by(user_id=db.session.scalar(select(User.id).where(User.username == os.environ.get('ADMIN_NAME')))).first():
            admin_role = UserRole(
                user_id = db.session.scalar(select(User.id).where(User.username == os.environ.get('ADMIN_NAME'))),
                role_id = db.session.scalar(select(Role.id).where(Role.name == 'Admin')))
            db.session.add(admin_role)
            db.session.commit()

class Role(db.Model):
    __tablename__ = "role"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(80), unique=True, nullable=False)
    users: Mapped[List['UserRole']] = relationship(back_populates='role')
    permissions: Mapped[List['RolePermission']] = relationship()

    @staticmethod
    def insert_roles(csv_file_path):
        with open(csv_file_path, mode='r', encoding='utf-8') as csvfile:
            data = csv.reader(csvfile)
            for role in data:
                name = role[0]
                if not Role.query.filter_by(name=name).first():
                    roles = Role(name=name)
                    db.session.add(roles)
            db.session.commit()


class RolePermission(db.Model):
    __tablename__ = 'role_permission'
    role_id: Mapped[int] = mapped_column(ForeignKey('role.id'), primary_key=True)
    permission_id: Mapped[int] = mapped_column(ForeignKey('permission.id'), primary_key=True)
    permission: Mapped['Permission'] = relationship()

    @staticmethod
    def insert_roles_permissions(csv_file_path):
        if not RolePermission.query.first():
            with open(csv_file_path, mode='r', encoding='utf-8') as csvfile:
                data = csv.reader(csvfile)
                for role_id, permission_id in data:
                        roles_permissions = RolePermission()
                        roles_permissions.role_id = role_id
                        roles_permissions.permission_id = permission_id
                        db.session.add(roles_permissions)
                db.session.commit()

class Permission(db.Model):
    __tablename__ = 'permission'
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(45))
    description: Mapped[str] = mapped_column(String(255))

    @staticmethod
    def insert_permissions(csv_file_path):
        with open(csv_file_path, mode='r', encoding='utf-8') as csvfile:
            data = csv.reader(csvfile)
            for name, description in data:
                if not Permission.query.filter_by(name=name).first():
                    permissions = Permission()
                    permissions.name = name
                    permissions.description = description
                    db.session.add(permissions)
            db.session.commit()

class UserSession(db.Model):
    __tablename__ = 'session'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    ip_address: Mapped[str] = mapped_column(String(45), nullable=True)
    last_activity: Mapped[datetime] = mapped_column(DateTime, nullable=True)

class SocialAccount(db.Model):
    __tablename__ = 'social_account'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    driver: Mapped[str] = mapped_column(String(45))
    driver_id: Mapped[str] = mapped_column(String(45))
    avatar_url: Mapped[str] = mapped_column(String(255))
    users: Mapped[list['User']] = relationship(back_populates='social_account')


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))