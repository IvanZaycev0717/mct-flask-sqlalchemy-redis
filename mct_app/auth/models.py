import csv
from datetime import datetime
import json
from typing import List, Optional
import os

from flask_login import AnonymousUserMixin, UserMixin
from itsdangerous.url_safe import URLSafeTimedSerializer
from itsdangerous import BadSignature
from sqlalchemy import (Boolean, DateTime,
                        Enum, ForeignKey,
                        Integer, JSON,
                        select, String,
                        UnicodeText)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from werkzeug.security import check_password_hash, generate_password_hash

from config import Is, Mood
from mct_app import db, login_manager
from flask import current_app


class User(UserMixin, db.Model):
    """Class for user model."""

    __tablename__ = "user"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    username: Mapped[str] = mapped_column(
        String(45),
        unique=True,
        nullable=False,
        index=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str] = mapped_column(String(120), nullable=False)
    phone: Mapped[str] = mapped_column(String(12), unique=True, nullable=True)
    has_social_account: Mapped[bool] = mapped_column(Boolean, default=False)

    roles: Mapped[List['UserRole']] = relationship(
        back_populates='user',
        cascade="all, delete-orphan")
    user_sessions: Mapped[List['UserSession']] = relationship(
        back_populates="user", cascade="all, delete-orphan")
    social_account: Mapped['SocialAccount'] = relationship(
        back_populates="user", cascade="all, delete-orphan")
    question: Mapped['Question'] = relationship(back_populates='user')
    answers: Mapped[List['Answer']] = relationship(
        back_populates='user',
        passive_deletes=True,
        lazy='joined')
    consultation: Mapped['Consultation'] = relationship(back_populates='user')
    user_statistics: Mapped['UserStatistics'] = relationship(
        back_populates='user',
        cascade="all, delete")
    user_diaries: Mapped[List['UserDiary']] = relationship(
        back_populates='user',
        cascade="all, delete")
    diary_recommendations: Mapped[List['DiaryRecommendation']] = relationship(
        back_populates='user',
        cascade="all, delete")

    def is_admin(self):
        """Check current user is the admin."""
        return self.roles[0].role_id == Is.ADMIN

    def is_content_manager(self):
        """Check current user is a content manager."""
        return self.roles[0].role_id == Is.CONTENT_MANAGER

    def is_doctor(self):
        """Check current user is a doctor."""
        return self.roles[0].role_id == Is.DOCTOR

    def is_patient(self):
        """Check current user is a patient."""
        return self.roles[0].role_id == Is.PATIENT

    @property
    def password(self):
        """Forbid to get user's password."""
        raise AttributeError('Пароль не должен быть получен')

    @password.setter
    def password(self, password):
        """Set hash of user's password."""
        self.password_hash = generate_password_hash(password)

    def verify_password(self, password):
        """Verify password correctness."""
        return check_password_hash(self.password_hash, password)

    @staticmethod
    def create_admin():
        """Create a new user as the admin."""
        if not User.query.filter_by(username=os.environ.get('ADMIN_NAME')
                                    ).first():
            admin = User(
                username=os.environ.get('ADMIN_NAME'),
                password=os.environ.get('ADMIN_PASS'),
                email=os.environ.get('ADMIN_EMAIL'))
            db.session.add(admin)
            db.session.commit()
            admin_statistics = UserStatistics(
                articles_statistics=json.dumps({}),
                textbook_statistics=json.dumps({}),
                user_id=Is.ADMIN
            )
            db.session.add(admin_statistics)
            db.session.commit()

    def reset_password(self, token, new_password):
        """Reset user's password."""
        s = URLSafeTimedSerializer(os.environ['SECRET_KEY'])
        try:
            data = s.loads(token)
        except BadSignature:
            current_app.logger.exception(
                "Token is Wrong while reseting password")
            return False
        if data.get('reset') != self.id:
            return False
        self.password = new_password
        db.session.add(self)
        db.session.commit()
        return True

    def generate_password_reset_token(self):
        """Generate token for reseting password."""
        s = URLSafeTimedSerializer(os.environ['SECRET_KEY'])
        return s.dumps({'reset': self.id})

    def __repr__(self) -> str:
        """Show user data in the terminal."""
        return f'User({self.id} {self.username})'

    def __str__(self) -> str:
        """Show user data on the website."""
        return f'User({self.id} {self.username})'


class UserRole(db.Model):
    """Class for intermediate table between User and Role."""

    __tablename__ = 'user_role'
    user_id: Mapped[int] = mapped_column(
        ForeignKey('user.id'),
        primary_key=True)
    role_id: Mapped[int] = mapped_column(
        ForeignKey('role.id'),
        primary_key=True)

    role: Mapped['Role'] = relationship(back_populates='users')
    user: Mapped['User'] = relationship(back_populates='roles')

    @staticmethod
    def create_admin_role():
        """Create the role of admin."""
        q = select(User.id).where(
            User.username == os.environ.get('ADMIN_NAME'))
        if not UserRole.query.filter_by(user_id=db.session.scalar(q)).first():
            admin_role = UserRole(user_id=Is.ADMIN, role_id=Is.ADMIN)
            db.session.add(admin_role)
        db.session.commit()


class Role(db.Model):
    """Class for user's role."""

    __tablename__ = "role"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(80), unique=True,
                                      nullable=False, index=True)
    description: Mapped[str] = mapped_column(String, nullable=False)

    users: Mapped[List['UserRole']] = relationship(back_populates='role')

    @staticmethod
    def insert_roles(csv_file_path):
        """Insert roles from CSV file into Role table."""
        roles = Role.query.all()
        if not roles:
            with open(csv_file_path, mode='r', encoding='utf-8') as csvfile:
                reader = csv.DictReader(csvfile)
                for row in reader:
                    roles = Role(**row)
                    db.session.add(roles)
            db.session.commit()

    def __repr__(self) -> str:
        """Show role in the terminal."""
        return f'Role({self.id} {self.name})'

    def __str__(self) -> str:
        """Show role on the website."""
        return f'Role({self.id} {self.name})'


class UserSession(db.Model):
    """Class for users session."""

    __tablename__ = 'session'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    ip_address: Mapped[str] = mapped_column(String(45), nullable=True)
    last_activity: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    attendance: Mapped[datetime] = mapped_column(Integer, nullable=False)
    user_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey('user.id'))

    user: Mapped[List['User']] = relationship(back_populates='user_sessions')


class SocialAccount(db.Model):
    """Class for registration via social platforms."""

    __tablename__ = 'social_account'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    platform: Mapped[str] = mapped_column(String, nullable=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey('user.id'))

    user: Mapped['User'] = relationship(back_populates='social_account')


class Question(db.Model):
    """Class for questions."""

    __tablename__ = 'question'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    anon_name: Mapped[str] = mapped_column(String(45), nullable=True)
    user_id: Mapped[int] = mapped_column(ForeignKey('user.id'), nullable=True)
    body: Mapped[str] = mapped_column(UnicodeText)
    date: Mapped[datetime] = mapped_column(DateTime, nullable=True, index=True)
    ip_address: Mapped[str] = mapped_column(String(45))

    answers: Mapped[List['Answer']] = relationship(
        back_populates='question',
        cascade='all, delete',
        lazy='joined')
    user: Mapped['User'] = relationship(
        back_populates='question',
        lazy='joined')

    def __repr__(self) -> str:
        """Show question instance in the terminal."""
        return f'Question({self.id} {self.body})'

    def __str__(self) -> str:
        """Show question instance on the website."""
        return f'{self.id} {self.body}'


class Answer(db.Model):
    """Class for answers."""

    __tablename__ = 'answer'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    body: Mapped[str] = mapped_column(UnicodeText)
    question_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey('question.id'))
    user_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey('user.id', ondelete='SET NULL'), nullable=True)

    user: Mapped[Optional['User']] = relationship(
        back_populates='answers', lazy='joined')
    question: Mapped[Optional['Question']] = relationship(
        back_populates='answers', lazy='joined')

    def __repr__(self) -> str:
        """Show Answer instance in the terminal."""
        return f'Answer({self.id} {self.body})'

    def __str__(self) -> str:
        """Show Answer instance on the website."""
        return f'Answer({self.id} {self.body})'


class Consultation(db.Model):
    """Class for consultations."""

    __tablename__ = 'consultation'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    first_name: Mapped[str] = mapped_column(String(25))
    last_name: Mapped[str] = mapped_column(String(25))
    phone: Mapped[str] = mapped_column(String(12))
    user_id: Mapped[int] = mapped_column(ForeignKey('user.id'), nullable=True)
    date: Mapped[datetime] = mapped_column(DateTime, nullable=True)

    user: Mapped['User'] = relationship(back_populates='consultation')


class UserStatistics(db.Model):
    """Class for user's statistics."""

    __tablename__ = 'user_statistics'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    articles_statistics: Mapped[dict[str]] = mapped_column(JSON)
    textbook_statistics: Mapped[dict[str]] = mapped_column(JSON)

    user_id: Mapped[int] = mapped_column(
        ForeignKey('user.id', ondelete='CASCADE'))
    user: Mapped['User'] = relationship(back_populates='user_statistics')


class UserDiary(db.Model):
    """Class for user's diary."""

    __tablename__ = 'user_diary'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    date: Mapped[datetime] = mapped_column(DateTime, index=True)
    mood: Mapped[List[str]] = mapped_column(Enum(Mood))
    record: Mapped[str] = mapped_column(UnicodeText)
    user_id: Mapped[int] = mapped_column(
        ForeignKey('user.id', ondelete='CASCADE'))
    user: Mapped['User'] = relationship(back_populates='user_diaries')
    diary_recommendations: Mapped[List['DiaryRecommendation']] = relationship(
        back_populates='user_diary', cascade="all, delete")

    def __repr__(self) -> str:
        """Show UserDiary instance in the terminal."""
        return f'UserDiary({self.user.username} Запись {self.id})'

    def __str__(self) -> str:
        """Show UserDiary instance on the website."""
        return f'UserDiary({self.user.username} Запись {self.id})'


class DiaryRecommendation(db.Model):
    """Class for recommendations for particular diary note."""

    __tablename__ = 'diary_recommendation'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    recommendation: Mapped[str] = mapped_column(UnicodeText)
    user_diary_id: Mapped[int] = mapped_column(
        ForeignKey('user_diary.id', ondelete='CASCADE'))
    user_id: Mapped[int] = mapped_column(
        ForeignKey('user.id', ondelete='CASCADE'))

    user_diary: Mapped['UserDiary'] = relationship(
        back_populates='diary_recommendations')
    user: Mapped['User'] = relationship(back_populates='diary_recommendations')


class AnonymousUser(AnonymousUserMixin):
    """Class for anonymous user."""

    def is_anonymous(self):
        """Check whether current user is anonymous."""
        return True

    def is_doctor(self):
        """Check whether current user is a doctor."""
        return False

    def is_admin(self):
        """Check whether current user is admin."""
        return False


login_manager.anonymous_user = AnonymousUser


@login_manager.user_loader
def load_user(user_id):
    """Load current user to get id."""
    return User.query.get(int(user_id))
