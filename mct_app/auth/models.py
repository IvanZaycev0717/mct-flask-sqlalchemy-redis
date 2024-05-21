import csv
import datetime
from typing import List, Optional
import os
import os.path as op


from flask import abort
from itsdangerous.url_safe import URLSafeTimedSerializer
from itsdangerous import BadSignature
from markupsafe import Markup
from sqlalchemy import Boolean, DateTime, Integer, String, ForeignKey, select
from sqlalchemy.orm import Mapped, mapped_column, relationship
from werkzeug.security import check_password_hash, generate_password_hash
from flask_login import UserMixin, current_user, AnonymousUserMixin
from flask_admin.contrib.sqla import ModelView
import flask_admin
from flask_admin import expose
from wtforms import ValidationError
from wtforms_alchemy.fields import QuerySelectMultipleField
from config import IMAGE_BASE_PATH, Is
from wtforms.validators import DataRequired
from flask_admin.menu import MenuLink
from flask_admin.form.upload import ImageUploadField
from config import IMAGE_REL_PATHS
from werkzeug.utils import secure_filename
from PIL import Image as  PillowImage, ImageOps



from mct_app import db, login_manager, admin
from mct_app.site.models import News, Image as MyImage


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

class CustomImageUploadField(ImageUploadField):

    def pre_validate(self, form):
        super(ImageUploadField, self).pre_validate(form)

        if self._is_uploaded_file(self.data):
            try:
                self.image = PillowImage.open(self.data)
            except Exception as e:
                raise ValidationError('Invalid image: %s' % e)
    
    def _save_file(self, data, filename):
        path = self._get_path(filename)

        if not op.exists(op.dirname(path)):
            os.makedirs(os.path.dirname(path), self.permission | 0o111)

        # Figure out format
        filename, format = self._get_save_format(filename, self.image)

        if self.image:
            if self.max_size:
                image = self._resize(self.image, self.max_size)
            else:
                image = self.image
            self._save_image(image, self._get_path(filename), format)
        else:
            data.seek(0)
            data.save(self._get_path(filename))

        self._save_thumbnail(data, filename, format)

        return filename

    def _resize(self, image, size):
        (width, height, force) = size

        if image.size[0] > width or image.size[1] > height:
            if force:
                return ImageOps.fit(self.image, (width, height), PillowImage.LANCZOS)
            else:
                thumb = self.image.copy()
                thumb.thumbnail((width, height), PillowImage.LANCZOS)
                return thumb

        return image

    def _save_image(self, image, path, format='webp'):
        image.convert('RGB')
        with open(path, 'wb') as fp:
            image.save(fp, format, optimize=True, quality=90)
 
    def _get_save_format(self, filename, image):
        if image.format not in self.keep_image_formats:
            name, ext = op.splitext(filename)
            filename = '%s.webp' % name
            return filename, 'WEBP'

        return filename, image.format

class NewsView(AccessView):
    column_display_pk = True
    page_size = 10
    column_formatters = {
        'image': lambda v, c, m, p: Markup(f'<img src="{m.image.path}" width="100" height="100">')
    }

    def scaffold_form(self):
        form_class = super(NewsView, self).scaffold_form()
        delattr(form_class, 'image')
        form_class.extra = CustomImageUploadField(
            'Загрузите картинку',
            validators=[DataRequired()],
            base_path=IMAGE_BASE_PATH['news'])
        return form_class
    
    def on_model_change(self, form, model: News, is_created: bool) -> None:
        filename = secure_filename(form.extra.data.__dict__['filename'])
        form.extra.data.save(os.path.join(IMAGE_BASE_PATH['news'], filename))
        my_image = MyImage(path=os.path.join(IMAGE_REL_PATHS['news'], filename))
        model.image = my_image
        super(NewsView, self).on_model_change(form, model, is_created)


class UserRoleView(AccessView):
    column_list = ['user.id', 'user.username', 'role.name']
    column_sortable_list = ['user.id', 'user.username', 'role.name']
    column_searchable_list = ['user.id', 'user.username']
    form_create_rules = ('user', 'role')
    form_edit_rules = ('user', 'role')

class UserSessionView(AccessView):
    column_list = ['user.id', 'user.username', 'last_activity', 'attendance', 'ip_address']
    column_sortable_list = ['user.id', 'last_activity', 'attendance']
    column_searchable_list = ['user.id', 'user.username']
    can_delete = False
    can_edit = False
    can_create = False

admin.add_link(MenuLink(name='На сайт', url='/'))
admin.add_view(UserView(User, db.session, 'Пользователи'))
admin.add_view(UserSessionView(UserSession, db.session, 'Сессии'))
admin.add_view(UserRoleView(UserRole, db.session, 'Роли пользователей'))
admin.add_view(NewsView(News, db.session, 'Новости'))
