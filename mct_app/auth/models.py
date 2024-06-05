import csv
from datetime import datetime
from typing import List, Optional
import os


from itsdangerous.url_safe import URLSafeTimedSerializer
from itsdangerous import BadSignature
from sqlalchemy import Boolean, DateTime, Integer, String, ForeignKey, UnicodeText, select
from sqlalchemy.orm import Mapped, mapped_column, relationship
from werkzeug.security import check_password_hash, generate_password_hash
from flask_login import UserMixin, AnonymousUserMixin


from config import Is
from mct_app import db, login_manager


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
    question: Mapped['Question'] = relationship(back_populates='user')
    answers: Mapped[List['Answer']] = relationship(back_populates='user')

    def is_admin(self):
        return self.roles[0].role_id == Is.ADMIN

    def is_content_manager(self):
        return self.roles[0].role_id == Is.CONTENT_MANAGER
    
    def is_doctor(self):
        return self.roles[0].role_id == Is.DOCTOR
    
    def is_patient(self):
        return self.roles[0].role_id == Is.PATIENT

    @property
    def password(self):
        raise AttributeError('Пароль не должен быть получен')

    @password.setter
    def password(self, password):
        self.password_hash = generate_password_hash(password)

    def verify_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    @staticmethod
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

    @staticmethod
    def create_admin_role():
        if not UserRole.query.filter_by(user_id=db.session.scalar(select(User.id).where(User.username == os.environ.get('ADMIN_NAME')))).first():
            admin_role = UserRole(
                user_id = db.session.scalar(select(User.id).where(User.username == os.environ.get('ADMIN_NAME'))),
                role_id = db.session.scalar(select(Role.id).where(Role.id==Is.ADMIN)))
            db.session.add(admin_role)
            db.session.commit()

class Role(db.Model):
    __tablename__ = "role"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(80), unique=True, nullable=False)
    description: Mapped[str] = mapped_column(String, nullable=False)

    users: Mapped[List['UserRole']] = relationship(back_populates='role')

    @staticmethod
    def insert_roles(csv_file_path):
        with open(csv_file_path, mode='r', encoding='utf-8') as csvfile:
            data = csv.reader(csvfile)
            for role in data:
                name = role[0]
                description = role[1]
                if not Role.query.filter_by(name=name).first():
                    roles = Role(name=name, description=description)
                    db.session.add(roles)
            db.session.commit()

    def __repr__(self) -> str:
        return f'{self.id} {self.name}'

    def __str__(self) -> str:
        return f'{self.id} {self.name}'



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

class Question(db.Model):
    __tablename__ = 'question'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    anon_name: Mapped[str] = mapped_column(String(45), nullable=True)
    user_id: Mapped[int] = mapped_column(ForeignKey('user.id'), nullable=True)
    body: Mapped[str] = mapped_column(UnicodeText)
    date: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    ip_address: Mapped[str] = mapped_column(String(45))

    answers: Mapped[List['Answer']] = relationship(back_populates='question')
    user: Mapped['User'] = relationship(back_populates='question')

class Answer(db.Model):
    __tablename__ = 'answer'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    body: Mapped[str] = mapped_column(UnicodeText)
    question_id: Mapped[Optional[int]] = mapped_column(ForeignKey('question.id'))
    user_id: Mapped[Optional[int]] = mapped_column(ForeignKey('user.id'))

    user: Mapped[Optional['User']] = relationship(back_populates='answers')
    question: Mapped[Optional['Question']] = relationship(back_populates='answers')


class AnonymousUser(AnonymousUserMixin):

    def is_anonymous(self):
        return True

    def is_admin(self):
        return False

login_manager.anonymous_user = AnonymousUser

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

