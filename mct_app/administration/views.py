import json
import os
import os.path as op
import uuid


import elasticsearch
import elastic_transport
from flask import (abort, Blueprint,
                   current_app, request,
                   send_from_directory, url_for)
import flask_admin
from flask_admin import expose
from flask_admin.contrib.sqla import ModelView
from flask_admin.menu import MenuLink
from flask_admin.form.upload import ImageUploadField
from flask_ckeditor import CKEditorField, upload_fail, upload_success
from flask_login import current_user
from markupsafe import Markup
from PIL import Image as PillowImage, ImageOps
from sqlalchemy.event import listens_for
from werkzeug.utils import secure_filename
from wtforms_alchemy.fields import QuerySelectMultipleField
from wtforms.validators import DataRequired


from config import (basedir,
                    FILE_BASE_PATH, FILE_REL_PATH)
from mct_app import admin, cache, csrf, db
from mct_app.administration.models import BannedIPs
from mct_app.auth.models import (Answer, Consultation,
                                 DiaryRecommendation, Question,
                                 Role, User, UserDiary,
                                 UserRole, UserSession,
                                 UserStatistics)
from mct_app.search import add_to_index
from mct_app.site.models import (Article, ArticleCard, ArticleImage,
                                 Image as MyImage, News,
                                 TextbookChapter,
                                 TextbookParagraph, TextbookParagraphImage)
from mct_app.utils import (generate_image_name, get_images_names,
                           save_banned_ip_file, save_image_as_webp)


administration = Blueprint('administration', __name__)


@administration.route('/files/<filename>')
@csrf.exempt
def uploaded_files(filename):
    """Upload images."""
    path = os.path.join(basedir, 'mct_app', 'files')
    return send_from_directory(path, filename)


@administration.route('/upload', methods=['POST'])
@csrf.exempt
def upload(format='webp'):
    """Upload and save images as WEBP."""
    image = request.files.get('upload')
    extension = image.filename.split('.')[-1].lower()
    if extension not in current_app.config.get('ALLOWED_EXTENSIONS'):
        return upload_fail(message='Это не изображение')
    unique_filename = str(uuid.uuid4())
    image.filename = unique_filename + '.' + format
    path = os.path.join(basedir, 'mct_app', 'files', image.filename)
    save_image_as_webp(image, path)
    url = url_for('administration.uploaded_files', filename=image.filename)
    return upload_success(url, filename=image.filename)


class AccessView(ModelView):
    """Class provides access for only admin to admin panel."""

    def is_accessible(self):
        """Check whether current user is admin or not."""
        return current_user.is_admin()


class MyAdminIndexView(flask_admin.AdminIndexView):
    """Class to forbid access for everyone to admin panel except admin."""

    @expose('/')
    def index(self):
        """Block access for everyone who isnt admin."""
        if not current_user.is_admin():
            abort(403)
        return super(MyAdminIndexView, self).index()


class UserView(AccessView):
    """Class for users model in admin panel."""

    column_display_pk = True
    column_sortable_list = ['id', 'username', 'has_social_account']
    column_searchable_list = ['id', 'username', 'email', 'phone']
    column_exclude_list = ['password_hash',]
    form_excluded_columns = ['password_hash',]

    def scaffold_form(self):
        """Return a form of user model."""
        form_class = super(UserView, self).scaffold_form()
        delattr(form_class, 'has_social_account')
        form_class.extra = QuerySelectMultipleField(
            label='Roles',
            query_factory=lambda: Role.query.all(),
            validators=[DataRequired()])
        return form_class

    def on_model_change(self, form, model: User, is_created: bool) -> None:
        """Allow to chose a role for an user."""
        user_role = UserRole()
        user_role.role = form.extra.data[0]
        model.roles.clear()
        model.roles.append(user_role)
        super(UserView, self).on_model_change(form, model, is_created)


class CustomImageUploadField(ImageUploadField):
    """Overridden class of ImageUploadField."""

    def _resize(self, image, size):
        (width, height, force) = size

        if image.size[0] > width or image.size[1] > height:
            if force:
                return ImageOps.fit(
                    self.image,
                    (width, height),
                    PillowImage.Resampling.LANCZOS)
            else:
                thumb = self.image.copy()
                thumb.thumbnail(
                    (width, height),
                    PillowImage.Resampling.LANCZOS)
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


def add_article_image(article_id, article_body):
    """Allow to add images to an article."""
    images_names = get_images_names(text=article_body)
    article = db.session.query(Article).filter_by(id=article_id).first()
    if images_names:
        for image_name in images_names:
            article_image = ArticleImage()
            image = MyImage(
                filename=image_name,
                absolute_path=os.path.join(FILE_BASE_PATH, image_name),
                relative_path=os.path.join(FILE_REL_PATH, image_name),
            )
            article_image.article = article
            image.articles.append(article_image)


class NewsView(AccessView):
    """Class for displaying news model in admin panel."""

    column_display_pk = True
    page_size = 10
    edit_template = 'admin/edit.html'
    column_default_sort = ('id', True)
    column_formatters = {
        'image': lambda v, c, m, p: Markup(
            f'<img src="{m.image.relative_path}" width="100" height="100">')
    }

    def on_form_prefill(self, form, id):
        """Prefill the News form."""
        model = self.get_one(id)
        if model:
            form.extra.data = model.image.relative_path

    def scaffold_form(self):
        """Return a News model form."""
        form_class = super(NewsView, self).scaffold_form()
        delattr(form_class, 'image')
        form_class.extra = CustomImageUploadField(
            'Загрузите картинку',
            validators=[DataRequired()],
            base_path=FILE_BASE_PATH,
            namegen=generate_image_name,
            max_size=(300, 300, True),
            allow_overwrite=False,)
        return form_class

    def on_model_change(self, form, model: News, is_created: bool) -> None:
        """Allow to create ot edit news."""
        filename = secure_filename(form.extra.data.__dict__['filename'])
        if is_created:
            my_image = MyImage(
                filename=filename,
                absolute_path=os.path.join(FILE_BASE_PATH, filename),
                relative_path=os.path.join(FILE_REL_PATH, filename))
            model.image = my_image
        else:
            model.image.filename = filename
            model.image.absolute_path = os.path.join(
                FILE_BASE_PATH, filename)
            model.image.relative_path = os.path.join(
                FILE_REL_PATH, filename)
        cache.clear()
        super(NewsView, self).on_model_change(form, model, is_created)


class UserRoleView(AccessView):
    """Class for view of UserRole model."""

    column_list = ['user.id', 'user.username', 'role.name']
    column_sortable_list = ['user.id', 'user.username', 'role.name']
    column_searchable_list = ['user.id', 'user.username']
    form_create_rules = ('user', 'role')
    form_edit_rules = ('user', 'role')


class UserSessionView(AccessView):
    """Class for view of UserSession model."""

    column_list = ['user.id', 'user.username',
                   'last_activity', 'attendance', 'ip_address']
    column_sortable_list = ['user.id', 'last_activity', 'attendance']
    column_searchable_list = ['user.id', 'user.username']
    can_delete = False
    can_edit = False
    can_create = False


class ArticleCardView(AccessView):
    """Class for view of ArticleCard model."""

    column_default_sort = ('id', True)
    form_excluded_columns = ('image', 'article')
    create_template = 'admin/edit.html'
    edit_template = 'admin/edit.html'

    column_formatters = {
        'image': lambda v, c, m, p: Markup(
            f'<img src="{m.image.relative_path}" width="100" height="100">'),
        'article':
        lambda v, c, m, p: m.article.body[:150] if m.article.body else None
    }

    def on_form_prefill(self, form, id):
        """Prefill ArticleCard form before editing."""
        model = self.get_one(id)
        if model:
            form.body.data = model.article.body
            form.card_image.data = model.image.relative_path

    def scaffold_form(self):
        """Allow to render decent ArticleCard form."""
        form_class = super(ArticleCardView, self).scaffold_form()
        form_class.card_image = CustomImageUploadField(
            'Загрузите картинку карточки',
            validators=[DataRequired()],
            base_path=FILE_BASE_PATH,
            namegen=generate_image_name,
            max_size=(300, 300, True),
            allow_overwrite=True,)
        form_class.body = CKEditorField()
        return form_class

    def on_model_change(self,
                        form,
                        model: ArticleCard,
                        is_created: bool) -> None:
        """Create of edit AricleCard and particular Article."""
        filename = secure_filename(form.card_image.data.__dict__['filename'])
        if is_created:
            # We are CREATING an articlecard and aricle
            # image of current card
            my_image = MyImage(
                filename=filename,
                absolute_path=os.path.join(
                    FILE_BASE_PATH, filename),
                relative_path=os.path.join(
                    FILE_REL_PATH, filename))
            model.image = my_image

            # a new article inside the card
            article = Article(title=model.title, body=form.body.data)
            model.article = article

            # fetch images inside article content
            image_names = get_images_names(model.article.body)
            if image_names:
                for image_name in image_names:
                    article_image = ArticleImage()
                    image = MyImage(
                        filename=image_name,
                        absolute_path=os.path.join(FILE_BASE_PATH, image_name),
                        relative_path=os.path.join(FILE_REL_PATH, image_name),
                    )
                    article_image.image = image
                    model.article.images.append(article_image)

            # update users statistics after adding a new article
            statistics = UserStatistics.query.all()
            for stat in statistics:
                stat_dict = json.loads(stat.articles_statistics)
                stat_dict.update({model.id: False})
                stat.articles_statistics = json.dumps(stat_dict)
            db.session.commit()

        else:
            # We are EDITING an articlecard and aricle
            # change image of the current card
            model.image.filename = filename
            model.image.absolute_path = os.path.join(
                FILE_BASE_PATH, filename)
            model.image.relative_path = os.path.join(
                FILE_REL_PATH, filename)

            # take articlecard title to current article
            model.article.title = model.title

            # change content of the article body
            model.article.body = form.body.data

            # get all images in article
            image_names = get_images_names(model.article.body)

            # Get images before editing
            prev_images = set()
            if model.article.images:
                prev_images = {
                    image.image.filename for image in model.article.images}

            # Remove deleted images in the article from DB
            image_on_delete = tuple(prev_images - set(image_names))
            deleted_images = db.session.query(MyImage).filter(
                MyImage.filename.in_(image_on_delete)).all()
            for image_obj in deleted_images:
                obj_to_delete = db.session.query(ArticleImage).get(
                    {'image_id': image_obj.id, 'article_id': model.article.id})
                if obj_to_delete:
                    db.session.delete(obj_to_delete)
            db.session.commit()

            # Get images after editing
            if image_names:
                # Add new images in the article to DB
                images_on_add = tuple(set(image_names) - prev_images)
                for image_name in images_on_add:
                    article_image = ArticleImage()
                    image = MyImage(filename=image_name,
                                    absolute_path=os.path.join(
                                        FILE_BASE_PATH, image_name),
                                    relative_path=os.path.join(
                                        FILE_REL_PATH, image_name))
                    article_image.image = image
                    model.article.images.append(article_image)
        cache.clear()
        super(ArticleCardView, self).on_model_change(form, model, is_created)

    def on_model_delete(self, model):
        """Delete chosen ArticleCard."""
        statistics = UserStatistics.query.all()
        for stat in statistics:
            stat_dict = json.loads(stat.articles_statistics)
            del stat_dict[str(model.article.id)]
            stat.articles_statistics = json.dumps(stat_dict)
        db.session.commit()
        cache.clear()
        return super().on_model_delete(model)


class TextbookChapterView(AccessView):
    """Class for view of TextbookChapter model."""

    form_excluded_columns = ('textbook_paragraphs', )

    def on_model_delete(self, model):
        """Delete chosen TextbookChapter."""
        deleted_keys = [
            paragraph.id for paragraph in model.textbook_paragraphs]
        statistics = UserStatistics.query.all()
        for stat in statistics:
            stat_dict = json.loads(stat.textbook_statistics)
            for id in deleted_keys:
                del stat_dict[str(id)]
            stat.textbook_statistics = json.dumps(stat_dict)
        db.session.commit()
        cache.clear()
        return super().on_model_delete(model)


class TextbookParagraphView(AccessView):
    """Class for view of TextbookParagraph."""

    form_excluded_columns = ('images', 'content')
    create_template = 'admin/edit-paragraph.html'
    edit_template = 'admin/edit-paragraph.html'

    column_formatters = {
        'content': lambda v, c, m, p: m.content[:150] if m.content else None
    }

    def on_form_prefill(self, form, id):
        """Prefill TExtbookParagraph form before editing."""
        model = self.get_one(id)
        if model:
            form.paragraph_content.data = model.content

    def scaffold_form(self):
        """Return a decent form of TextbookParagraph."""
        form_class = super(TextbookParagraphView, self).scaffold_form()
        form_class.paragraph_content = CKEditorField()
        return form_class

    def on_model_change(self,
                        form,
                        model: TextbookParagraph,
                        is_created: bool) -> None:
        """Allow to create and edit TextbookParagraph."""
        if is_created:
            # We are CREATING a new paragraph in the textbook
            model.content = form.paragraph_content.data

            # get new images in the current paragraph
            image_names = get_images_names(model.content)
            if image_names:
                for image_name in image_names:
                    paragraph_image = TextbookParagraphImage()
                    image = MyImage(
                        filename=image_name,
                        absolute_path=os.path.join(FILE_BASE_PATH, image_name),
                        relative_path=os.path.join(FILE_REL_PATH, image_name),
                    )
                    paragraph_image.image = image
                    model.images.append(paragraph_image)

            # update users statistics after adding a new article
            statistics = UserStatistics.query.all()
            for stat in statistics:
                stat_dict = json.loads(stat.textbook_statistics)
                stat_dict.update({model.id: False})
                stat.textbook_statistics = json.dumps(stat_dict)
            db.session.commit()
        else:
            # We are EDITING a paragraph in the textbook
            # write paragraph content to model content
            model.content = form.paragraph_content.data

            # get all images in the content
            image_names = get_images_names(model.content)

            # Get images before editing
            prev_images = set()
            if model.images:
                prev_images = {image.image.filename for image in model.images}

            # Remove deleted images in the paragraph from DB
            image_on_delete = tuple(prev_images - set(image_names))
            deleted_images = db.session.query(MyImage).filter(
                MyImage.filename.in_(image_on_delete)).all()
            for image_obj in deleted_images:
                obj_to_delete = db.session.query(TextbookParagraphImage).get(
                    {
                        'image_id': image_obj.id,
                        'textbook_paragraph_id': model.id})
                if obj_to_delete:
                    db.session.delete(obj_to_delete)
            db.session.commit()

            # Get images after editing
            if image_names:
                # Add new images in the article to DB
                images_on_add = tuple(set(image_names) - prev_images)
                for image_name in images_on_add:
                    paragraph_image = TextbookParagraphImage()
                    image = MyImage(
                        filename=image_name,
                        absolute_path=os.path.join(FILE_BASE_PATH, image_name),
                        relative_path=os.path.join(FILE_REL_PATH, image_name),
                    )
                    paragraph_image.image = image
                    model.images.append(paragraph_image)
        try:
            add_to_index(model.__tablename__, model)
        except elastic_transport.ConnectionError:
            current_app.logger.exception(
                'Paragrapth created without Elasticsearch')
        except elasticsearch.NotFoundError:
            current_app.logger.exception('Paragrapth has no Elasticsearch')
        cache.clear()
        super(TextbookParagraphView, self).on_model_change(
            form,
            model,
            is_created)

    def on_model_delete(self, model):
        """Detete chosen TextbookParagraph."""
        statistics = UserStatistics.query.all()
        for stat in statistics:
            stat_dict = json.loads(stat.textbook_statistics)
            del stat_dict[str(model.id)]
            stat.textbook_statistics = json.dumps(stat_dict)
        db.session.commit()
        try:
            TextbookParagraph.reindex()
        except elastic_transport.ConnectionError:
            current_app.logger.exception(
                'Paragrapth deleted without Elasticsearch')
        except elasticsearch.NotFoundError:
            current_app.logger.exception('Paragrapth has no Elasticsearch')
        cache.clear()
        return super().on_model_delete(model)


class BannedIPsView(AccessView):
    """Class for view of BannedIPs in admin panel."""

    can_edit = False

    def on_model_change(self, form, model, is_created: bool) -> None:
        """Allow to create or edit banned IPs."""
        banned_ip = [ip.banned_ip for ip in BannedIPs.query.all()]
        if form.banned_ip.data not in banned_ip:
            banned_ip.append(form.banned_ip.data)
        save_banned_ip_file(banned_ip)
        super(BannedIPsView, self).on_model_change(form, model, is_created)

    def on_model_delete(self, model):
        """Allow to delete banned IPs."""
        banned_ip = [ip.banned_ip for ip in BannedIPs.query.all()]
        if model.banned_ip in banned_ip:
            banned_ip.remove(model.banned_ip)
        save_banned_ip_file(banned_ip)
        return super().on_model_delete(model)


# SQLAlchemy Events
@listens_for(News, 'after_delete')
def delete_unused_news_images(mapper, connection, target: News):
    """Delete image from SSD after database deletion of this image."""
    if target:
        try:
            os.remove(target.image.absolute_path)
        except OSError:
            current_app.logger.exception(
                'News images arent deleted after news deleting')


@listens_for(News, 'before_update')
def delete_unused_news_images_before_update(mapper, connection, target: News):
    """Delete image from SSD before database update of a new image."""
    if target:
        try:
            os.remove(target.image.absolute_path)
        except OSError:
            current_app.logger.exception(
                'Unused News images arent deleted after update')


@listens_for(ArticleCard, 'after_delete')
def delete_unused_articlecard_images(mapper, connection, target: ArticleCard):
    """Delete image from SSD after database deletion of this image."""
    if target:
        try:
            os.remove(target.image.absolute_path)
            if target.article.images:
                for article_image in target.article.images:
                    os.remove(article_image.image.absolute_path)
        except OSError:
            current_app.logger.exception(
                'Unused ArticleCard images arent'
                ' deleted after article deleting')


@listens_for(ArticleCard, 'before_update')
def delete_unused_articlecard_images_before_update(mapper,
                                                   connection,
                                                   target: ArticleCard):
    """Delete image from SSD before database update of a new image."""
    if target:
        try:
            os.remove(target.image.absolute_path)
        except OSError:
            current_app.logger.exception(
                'Unused ArticleCard images arent'
                ' deleted after article updating')


@listens_for(TextbookParagraph, 'after_delete')
def delete_unused_textbookparagraph_images(mapper,
                                           connection,
                                           target: TextbookParagraph):
    """Delete image from SSD after database deletion of this image."""
    if target:
        try:
            if target.images:
                for image in target.images:
                    os.remove(image.image.absolute_path)
        except OSError:
            current_app.logger.exception(
                'Unused TextbookParagraph images'
                ' arent deleted after article deleting')


@listens_for(db.session, 'after_flush')
def delete_images_from_content(session, flush_content):
    """Delete unused anymore images from Articles or TextbookParagraph."""
    if session.deleted:
        try:
            for item in session.deleted:
                if isinstance(item, ArticleImage):
                    os.remove(item.image.absolute_path)
                if isinstance(item, TextbookParagraphImage):
                    os.remove(item.image.absolute_path)
        except OSError:
            current_app.logger.exception(
                'Unused TextbookPar/Article images'
                ' arent deleted after article deleting')


# Admin view fill
admin.add_link(MenuLink(name='На сайт', url='/'))
admin.add_view(UserView(User, db.session, 'Пользователи'))
admin.add_view(UserSessionView(UserSession, db.session, 'Сессии'))
admin.add_view(UserRoleView(UserRole, db.session, 'Роли пользователей'))
admin.add_view(NewsView(News, db.session, 'Новости'))
admin.add_view(ArticleCardView(ArticleCard, db.session, 'Статьи'))
admin.add_view(TextbookChapterView(
    TextbookChapter, db.session, 'Разделы учебника'))
admin.add_view(TextbookParagraphView(
    TextbookParagraph, db.session, 'Главы учебника'))
admin.add_view(AccessView(Question, db.session, 'Вопросы'))
admin.add_views(AccessView(Answer, db.session, 'Ответы'))
admin.add_views(AccessView(UserDiary, db.session, 'Дневник пользователя'))
admin.add_views(AccessView(DiaryRecommendation, db.session, 'Рекомендации'))
admin.add_views(AccessView(Consultation, db.session, 'Консультации'))
admin.add_views(BannedIPsView(BannedIPs, db.session, 'Забанить по IP'))
