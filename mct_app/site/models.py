from datetime import datetime
from typing import List

import elastic_transport
from flask import current_app
from sqlalchemy import (DateTime, ForeignKey, Integer,
                        select, String, Text, UnicodeText)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from mct_app import db
from mct_app.search import add_to_index, query_index, remove_from_index


class SearchableMixin:
    """Class for mixin to use Elasticsearch."""

    @classmethod
    def search(cls, expression, page, per_page):
        """Search some full text in Elasticsearch."""
        ids, total = query_index(cls.__tablename__, expression, page, per_page)
        if total == 0:
            return [], 0
        when = []
        for i in range(len(ids)):
            when.append((ids[i], i))
        query = select(cls).where(cls.id.in_(ids)).order_by(
            db.case(*when, value=cls.id))
        return db.session.scalars(query), total

    @classmethod
    def before_commit(cls, session):
        """Choose action working with Elasticsearch."""
        session._changes = {
            'add': list(session.new),
            'update': list(session.dirty),
            'delete': list(session.deleted)
        }

    @classmethod
    def after_commit(cls, session):
        """Do automatically some action after commit."""
        try:
            for obj in session._changes['add']:
                if isinstance(obj, SearchableMixin):
                    add_to_index(obj.__tablename__, obj)
            for obj in session._changes['update']:
                if isinstance(obj, SearchableMixin):
                    add_to_index(obj.__tablename__, obj)
            for obj in session._changes['delete']:
                if isinstance(obj, SearchableMixin):
                    remove_from_index(obj.__tablename__, obj)
            session._changes = None
        except elastic_transport.ConnectionError:
            current_app.logger.exception('Elasticsearch server doesnt work')

    @classmethod
    def reindex(cls):
        """Reindex all the indecies in Elasticsearch."""
        for obj in db.session.scalars(select(cls)):
            add_to_index(cls.__tablename__, obj)


class Image(db.Model):
    """Class for image model."""

    __tablename__ = 'image'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    filename: Mapped[str] = mapped_column(String)
    absolute_path: Mapped[str] = mapped_column(String(255))
    relative_path: Mapped[str] = mapped_column(String(255))

    news: Mapped['News'] = relationship(back_populates='image')
    article_card: Mapped['ArticleCard'] = relationship(back_populates='image')
    articles: Mapped[List['ArticleImage']] = relationship(
        back_populates='image')
    textbook_paragraphs: Mapped[List['TextbookParagraphImage']] = relationship(
        back_populates='image')

    def __repr__(self) -> str:
        """Show an image's filename in the terminal."""
        return f'{self.__class__.__name__}(file={self.filename})'


class ArticleCard(db.Model):
    """Class for an article card."""

    __tablename__ = 'article_card'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(255))
    description: Mapped[str] = mapped_column(String(255))
    last_update: Mapped[datetime] = mapped_column(DateTime, index=True)
    image_id: Mapped[int] = mapped_column(
        ForeignKey('image.id', ondelete='CASCADE'))
    article_id: Mapped[int] = mapped_column(
        ForeignKey('article.id', ondelete='CASCADE'))

    image: Mapped['Image'] = relationship(
        back_populates='article_card', cascade='all, delete')
    article: Mapped['Article'] = relationship(
        back_populates='article_card', cascade='all, delete')


class Article(db.Model):
    """Class for a single article."""

    __tablename__ = 'article'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(255))
    body: Mapped[str] = mapped_column(UnicodeText)

    article_card: Mapped['ArticleCard'] = relationship(
        back_populates='article')
    images: Mapped[List['ArticleImage']] = relationship(
        back_populates='article', cascade='all, delete')

    def __repr__(self) -> str:
        """Show article body in the terminal."""
        return f'{self.__class__.__name__} - {self.body}'


class ArticleImage(db.Model):
    """Class for intermediate table between Article and Image."""

    __tablename__ = 'article_image'

    article_id: Mapped[int] = mapped_column(
        ForeignKey('article.id', ondelete='CASCADE'), primary_key=True)
    image_id: Mapped[int] = mapped_column(
        ForeignKey('image.id', ondelete='CASCADE'), primary_key=True)

    article: Mapped['Article'] = relationship(back_populates='images')
    image: Mapped['Image'] = relationship(
        back_populates='articles', cascade='all, delete')


class News(db.Model):
    """Class for news."""

    __tablename__ = 'news'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(255))
    content: Mapped[str] = mapped_column(Text)
    last_update: Mapped[datetime] = mapped_column(DateTime, index=True)
    image_id: Mapped[int] = mapped_column(
        ForeignKey('image.id', ondelete='CASCADE'))

    image: Mapped['Image'] = relationship(
        back_populates='news', cascade='all, delete')


class TextbookChapter(db.Model):
    """Class for a textbook chapter."""

    __tablename__ = 'textbook_chapter'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str] = mapped_column(String(255), nullable=True)

    textbook_paragraphs: Mapped[List['TextbookParagraph']] = relationship(
        back_populates='textbook_chapter', passive_deletes=True)

    def __repr__(self) -> str:
        """Show name of textbook chapter in the terminal."""
        return f'{self.__class__.__name__}({self.name})'


class TextbookParagraph(SearchableMixin, db.Model):
    """Class for a textbook paragraph."""

    __tablename__ = 'textbook_paragraph'
    __searchable__ = ['content']

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    content: Mapped[str] = mapped_column(UnicodeText)
    textbook_chapter_id: Mapped[int] = mapped_column(
        ForeignKey('textbook_chapter.id', ondelete='SET NULL'), nullable=True)

    images: Mapped[List['TextbookParagraphImage']] = relationship(
        back_populates='textbook_paragraph', cascade='all, delete')
    textbook_chapter: Mapped['TextbookChapter'] = relationship(
        back_populates='textbook_paragraphs')

    def __repr__(self) -> str:
        """Show name of textbook paragraph in the terminal."""
        return f'{self.__class__.__name__}({self.name})'


class TextbookParagraphImage(db.Model):
    """Class for intermediate table between TextbooParagraph and Image."""

    __tablename__ = 'textbook_paragraph_image'

    image_id: Mapped[int] = mapped_column(
        ForeignKey('image.id', ondelete='CASCADE'), primary_key=True)
    textbook_paragraph_id: Mapped[int] = mapped_column(
        ForeignKey('textbook_paragraph.id', ondelete='CASCADE'),
        primary_key=True)

    image: Mapped['Image'] = relationship(
        back_populates='textbook_paragraphs', cascade='all, delete')
    textbook_paragraph: Mapped['TextbookParagraph'] = relationship(
        back_populates='images')


db.event.listen(db.session, 'before_commit', SearchableMixin.before_commit)
db.event.listen(db.session, 'after_commit', SearchableMixin.after_commit)
