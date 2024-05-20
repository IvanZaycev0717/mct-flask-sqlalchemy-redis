import csv
import datetime
from typing import List, Optional
import os

from flask import abort, url_for
from itsdangerous.url_safe import URLSafeTimedSerializer
from itsdangerous import BadSignature
from sqlalchemy import Boolean, DateTime, Integer, String, ForeignKey, select
from sqlalchemy.orm import Mapped, mapped_column, relationship
from werkzeug.security import check_password_hash, generate_password_hash
from flask_login import UserMixin, current_user, AnonymousUserMixin
from flask_admin.contrib.sqla import ModelView
import flask_admin
from flask_admin import expose
from wtforms import SelectField, StringField
from wtforms_alchemy import ModelForm
from wtforms_alchemy.fields import QuerySelectMultipleField
from config import Is
from flask_admin.form import SecureForm
from wtforms.validators import DataRequired
from flask_admin.menu import MenuLink

from mct_app import db, login_manager, admin


class User(UserMixin, db.Model):
    __tablename__ = "user"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    username: Mapped[str] = mapped_column(
        String(45),
        unique=True,
        nullable=False
        )
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str] = mapped_column(String(120), nullable=False)
    phone: Mapped[str] = mapped_column(String(12), unique=True, nullable=True)
    has_social_account: Mapped[bool] = mapped_column(Boolean, default=False)

    roles: Mapped[List['UserRole']] = relationship(back_populates='user', cascade="all, delete-orphan")
    user_sessions: Mapped[List['UserSession']] = relationship(
        back_populates="user", cascade="all, delete-orphan"
        )
    social_account: Mapped['SocialAccount'] = relationship(
        back_populates="user", cascade="all, delete-orphan"
        )

    def is_admin(self):
        return self.roles[0].role_id == Is.ADMIN

    @property
    def password(self):
        raise AttributeError('Пароль не должен быть получен')

    @password.setter
    def password(self, password):
        self.password_hash = generate_password_hash(password)

    def verify_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def create_admin():
        if not User.query.filter_by(username=os.environ.get('ADMIN_NAME')
                                    ).first():
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
    


    def __repr__(self) -> str:
        return f'{self.id} {self.username}'

    def __str__(self) -> str:
        return f'{self.id} {self.username}'
        

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
    
    def __repr__(self) -> str:
        return f'{self.id} {self.name}'
    
    def __str__(self) -> str:
        return f'{self.id} {self.name}'


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
    user_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey('user.id'))

    user: Mapped[List['User']] = relationship(back_populates='user_sessions')

class SocialAccount(db.Model):
    __tablename__ = 'social_account'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    platform: Mapped[str] = mapped_column(String, nullable=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey('user.id'))

    user: Mapped['User'] = relationship(back_populates='social_account')

class AnonymousUser(AnonymousUserMixin):

    def is_anonymous(self):
        return True

    def is_admin(self):
        return False

login_manager.anonymous_user = AnonymousUser

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


class AccessView(ModelView):

    def is_accessible(self):
        return current_user.is_admin()


class MyAdminIndexView(flask_admin.AdminIndexView):
    @expose('/')
    def index(self):
        if not current_user.is_admin():
            abort(403)
        return super(MyAdminIndexView, self).index()

    def get_admin_menu(self):
        menu = super(MyAdminIndexView, self).get_admin_menu()
        menu.append(MenuLink(name='Go to Main Page', url='/'))
        return menu


class UserView(AccessView):
    column_display_pk = True
    column_sortable_list = ['id', 'username', 'has_social_account']
    column_searchable_list = ['id', 'username', 'email', 'phone']
    column_exclude_list = ['password_hash',]

    def scaffold_form(self):
        form_class = super(UserView, self).scaffold_form()
        delattr(form_class, 'has_social_account')
        form_class.extra = QuerySelectMultipleField(label='Roles', query_factory=lambda: Role.query.all(), validators=[DataRequired()])
        return form_class

    def on_model_change(self, form, model: User, is_created: bool) -> None:
        model.password_hash = generate_password_hash(form.password_hash.data)
        user_role = UserRole()
        user_role.role = form.extra.data[0]
        model.roles.clear()
        model.roles.append(user_role)
        super(UserView, self).on_model_change(form, model, is_created)

class UserRoleView(AccessView):
    column_list = ['user.id', 'user.username', 'role.name']
    column_sortable_list = ['user.id', 'user.username', 'role.name']
    column_searchable_list = ['user.id', 'user.username']
    form_create_rules = ('user', 'role')

class UserSessionView(AccessView):
    column_list = ['user.id', 'user.username', 'last_activity', 'attendance', 'ip_address']
    column_sortable_list = ['user.id', 'last_activity', 'attendance']
    column_searchable_list = ['user.id', 'user.username']
    can_delete = False
    can_edit = False
    can_create = False


admin.add_view(UserView(User, db.session, 'Пользователи'))
admin.add_view(UserSessionView(UserSession, db.session, 'Сессии'))
admin.add_view(UserRoleView(UserRole, db.session, 'Роли пользователей'))
