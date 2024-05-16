import csv
import datetime
import json
from typing import List, Optional
import os

from itsdangerous.url_safe import URLSafeTimedSerializer
from itsdangerous import BadSignature
from sqlalchemy import Boolean, DateTime, Integer, String, ForeignKey, select, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from werkzeug.security import check_password_hash, generate_password_hash
from flask_login import UserMixin

from mct_app import db, login_manager

class User(UserMixin, db.Model):
    __tablename__ = "user"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    username: Mapped[str] = mapped_column(String(45), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str] = mapped_column(String(120), nullable=False)
    phone: Mapped[str] = mapped_column(String(12), unique=True, nullable=True)
    has_social_account: Mapped[bool] = mapped_column(Boolean, default=False)

    roles: Mapped[List['UserRole']] = relationship(back_populates="user")
    user_sessions: Mapped[List['UserSession']] = relationship(back_populates="user")
    social_account: Mapped['SocialAccount'] = relationship(back_populates="user")

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
    
    def reset_password(self, token, new_password):
        s = URLSafeTimedSerializer(os.environ['SECRET_KEY'])
        try:
            data = s.loads(token)
        except BadSignature:
            return False
        if data.get('reset') != self.id:
            return False
        self.password = new_password
        db.session.add(self)
        db.session.commit()
        return True
    
    def generate_password_reset_token(self):
        s = URLSafeTimedSerializer(os.environ['SECRET_KEY'])
        return s.dumps({'reset': self.id})
        


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
    attendance: Mapped[datetime] = mapped_column(Integer, nullable=False)

    user_id: Mapped[Optional[int]] = mapped_column(ForeignKey('user.id'))
    user: Mapped[List['User']] = relationship(back_populates='user_sessions')

class SocialAccount(db.Model):
    __tablename__ = 'social_account'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    platform: Mapped[str] = mapped_column(String, nullable=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey('user.id'))
    user: Mapped['User'] = relationship(back_populates='social_account')


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))