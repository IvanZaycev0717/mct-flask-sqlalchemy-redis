import uuid
import os
import os.path as op


from flask import Blueprint, request, send_from_directory, url_for
from flask_ckeditor import upload_success, upload_fail
from flask import abort, url_for
from markupsafe import Markup
from werkzeug.security import generate_password_hash
from flask_login import current_user
from flask_admin.contrib.sqla import ModelView
import flask_admin
from flask_admin import expose
from wtforms_alchemy.fields import QuerySelectMultipleField
from config import ALLOWED_EXTENSIONS, IMAGE_BASE_PATH
from wtforms.validators import DataRequired
from flask_admin.menu import MenuLink
from flask_admin.form.upload import ImageUploadField
from config import IMAGE_REL_PATHS
from werkzeug.utils import secure_filename
from PIL import Image as  PillowImage, ImageOps
from sqlalchemy.event import listens_for
from flask_ckeditor import CKEditorField


from mct_app.auth.models import *
from mct_app import db, admin
from mct_app.site.models import ArticleCard, News, Image as MyImage, Article
from mct_app import db
from mct_app.site.models import Article, ArticleCard, News
from config import IMAGE_BASE_PATH, IMAGE_REL_PATHS, basedir
from mct_app import csrf
from mct_app.utils import save_image_as_webp

administration = Blueprint('administration', __name__)


@administration.route('/files/<filename>')
@csrf.exempt
def uploaded_files(filename):
    path = os.path.join(basedir, 'mct_app', 'files')
    return send_from_directory(path, filename)

@administration.route('/upload', methods=['POST'])
@csrf.exempt
def upload(format='webp'):
    image = request.files.get('upload')
    extension = image.filename.split('.')[-1].lower()
    if extension not in ALLOWED_EXTENSIONS:
        return upload_fail(message='Это не изображение')
    unique_filename = str(uuid.uuid4())
    image.filename = unique_filename + '.' + format
    path = os.path.join(basedir, 'mct_app', 'files', image.filename)
    save_image_as_webp(image, path)
    url = url_for('administration.uploaded_files', filename=image.filename)
    return upload_success(url, filename=image.filename)

@administration.route('/delete-image', methods=['POST'])
@csrf.exempt
def delete_image():
    image_src = request.form.get('image_src')
    print(image_src)

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


def generate_image_name(obj, file_data):
    image_suffix = uuid.uuid4()
    return secure_filename(f"image_{image_suffix}")


class CustomImageUploadField(ImageUploadField):

    def _resize(self, image, size):
        (width, height, force) = size

        if image.size[0] > width or image.size[1] > height:
            if force:
                return ImageOps.fit(self.image, (width, height), PillowImage.Resampling.LANCZOS)
            else:
                thumb = self.image.copy()
                thumb.thumbnail((width, height), PillowImage.Resampling.LANCZOS)
                return thumb

        return image

    def _save_image(self, image, path, format='WEBP'):
        # New Pillow versions require RGB format for JPEGs
        if format == 'JPEG' and image.mode != 'RGB':
            image = image.convert('RGB')
        elif image.mode not in ('RGB', 'RGBA'):
            image = image.convert('RGBA')

        with open(path, 'wb') as fp:
            image.save(fp, format, quality=90, method=0)

    def _get_save_format(self, filename, image):
        if image.format not in self.keep_image_formats:
            name, ext = op.splitext(filename)
            filename = '%s.webp' % name
            return filename, 'WEBP'

        return filename, image.format


@listens_for(News, 'after_delete')
def receive_after_delete(mapper, connection, target):
    "listen for the 'after_delete' event"
    if target:
        try:
            os.remove(target.image.absolute_path)
        except OSError:
            pass

@listens_for(ArticleCard, 'after_delete')
def delete_article_files(mapper, connection, target):
    "listen for the 'after_delete' event"
    if target:
        try:
            os.remove(target.image.absolute_path)
        except OSError:
            pass

@listens_for(ArticleCard, 'before_update')
def update_image_event(mapper, connection, target):
    if target:
        try:
            os.remove(target.image.absolute_path)
        except OSError:
            pass

class NewsView(AccessView):
    column_display_pk = True
    page_size = 10
    column_default_sort = ('id', True)
    column_formatters = {
        'image': lambda v, c, m, p: Markup(f'<img src="{m.image.relative_path}" width="100" height="100">')
    }

    def scaffold_form(self):
        form_class = super(NewsView, self).scaffold_form()
        delattr(form_class, 'image')
        form_class.extra = CustomImageUploadField(
            'Загрузите картинку',
            validators=[DataRequired()],
            base_path=IMAGE_BASE_PATH['news'],
            namegen=generate_image_name,
            max_size=(300, 300, True)
            )
        return form_class


    def on_model_change(self, form, model: News, is_created: bool) -> None:
        filename = secure_filename(form.extra.data.__dict__['filename'])
        my_image = MyImage(
            filename=filename,
            absolute_path=os.path.join(IMAGE_BASE_PATH['news'], filename),
            relative_path=os.path.join(IMAGE_REL_PATHS['news'], filename))
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



class ArticleCardView(AccessView):
    column_default_sort = ('id', True)
    form_excluded_columns = ('image', 'article')
    create_template = 'admin/edit.html'
    edit_template = 'admin/edit.html'

    column_formatters = {
        'image': lambda v, c, m, p: Markup(f'<img src="{m.image.relative_path}" width="100" height="100">')
    }

    def on_form_prefill(self, form, id):
        model = self.get_one(id)
        if model:
            form.body.data = model.article.body

    def scaffold_form(self):
        form_class = super(ArticleCardView, self).scaffold_form()
        form_class.card_image = CustomImageUploadField(
            'Загрузите картинку карточки',
            validators=[DataRequired()],
            base_path=IMAGE_BASE_PATH['articles'],
            namegen=generate_image_name,
            max_size=(300, 300, True),
            allow_overwrite=False,
            )
        form_class.body = CKEditorField()
        return form_class

    def on_model_change(self, form, model: ArticleCard, is_created: bool) -> None:
        filename = secure_filename(form.card_image.data.__dict__['filename'])
        if is_created:
            my_image = MyImage(
                filename=filename,
                absolute_path=os.path.join(IMAGE_BASE_PATH['articles'], filename),
                relative_path=os.path.join(IMAGE_REL_PATHS['articles'], filename))
            article = Article(title=model.title, body=form.body.data)
            model.article = article
            model.image = my_image
        else:
            model.image.filename = filename
            model.image.absolute_path = os.path.join(IMAGE_BASE_PATH['articles'], filename)
            model.image.relative_path = os.path.join(IMAGE_REL_PATHS['articles'], filename)
            model.article.title = model.title
            model.article.body = form.body.data
        super(ArticleCardView, self).on_model_change(form, model, is_created)



admin.add_link(MenuLink(name='На сайт', url='/'))
admin.add_view(UserView(User, db.session, 'Пользователи'))
admin.add_view(UserSessionView(UserSession, db.session, 'Сессии'))
admin.add_view(UserRoleView(UserRole, db.session, 'Роли пользователей'))
admin.add_view(NewsView(News, db.session, 'Новости'))
admin.add_view(ArticleCardView(ArticleCard, db.session, 'Статьи'))