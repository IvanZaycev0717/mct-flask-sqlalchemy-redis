from datetime import datetime
from typing import List, Optional


from sqlalchemy import DateTime, Integer, String, ForeignKey, UnicodeText, Text, select
from sqlalchemy.orm import Mapped, mapped_column, relationship


from mct_app import db
from mct_app.search import add_to_index, remove_from_index, query_index


class SearchableMixin:
    @classmethod
    def search(cls, expression, page, per_page):
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
        session._changes = {
            'add': list(session.new),
            'update': list(session.dirty),
            'delete': list(session.deleted)
        }

    @classmethod
    def after_commit(cls, session):
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

    @classmethod
    def reindex(cls):
        for obj in db.session.scalars(select(cls)):
            add_to_index(cls.__tablename__, obj)


class Image(db.Model):
    __tablename__ = "image"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    filename: Mapped[str] = mapped_column(String)
    absolute_path: Mapped[str] = mapped_column(String(255))
    relative_path: Mapped[str] = mapped_column(String(255))

    news: Mapped['News'] = relationship(back_populates='image')
    article_card: Mapped['ArticleCard'] = relationship(back_populates='image')
    articles: Mapped[List['ArticleImage']] = relationship(back_populates='image')
    textbook_paragraphs: Mapped[List['TextbookParagraphImage']] = relationship(back_populates='image')

    def __repr__(self) -> str:
        return str(self.filename)

    def __str__(self) -> str:
        return f'{self.filename}'
    

class ArticleCard(db.Model):
    __tablename__ = 'article_card'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(255))
    description: Mapped[str] = mapped_column(String(255))
    last_update: Mapped[datetime] = mapped_column(DateTime)
    image_id: Mapped[int] = mapped_column(ForeignKey('image.id', ondelete='CASCADE'))
    article_id: Mapped[int] = mapped_column(ForeignKey('article.id', ondelete='CASCADE'))

    image: Mapped['Image'] = relationship(back_populates='article_card', cascade="all, delete")
    article: Mapped['Article'] = relationship(back_populates='article_card', cascade="all, delete")


class Article(SearchableMixin, db.Model):
    __tablename__ = 'article'
    __searchable__ = ['body']

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(255))
    body: Mapped[str] = mapped_column(UnicodeText)

    article_card: Mapped['ArticleCard'] = relationship(back_populates='article')
    images: Mapped[List['ArticleImage']] = relationship(back_populates='article', cascade='all, delete')

    def __repr__(self) -> str:
        return str(self.body)

    def __str__(self) -> str:
        return f'{self.title} {self.body}'

class ArticleImage(db.Model):
    __tablename__ = 'article_image'

    article_id: Mapped[int] = mapped_column(ForeignKey('article.id', ondelete='CASCADE'), primary_key=True)
    image_id: Mapped[int] = mapped_column(ForeignKey('image.id', ondelete='CASCADE'), primary_key=True)

    article: Mapped['Article'] = relationship(back_populates='images')
    image: Mapped['Image'] = relationship(back_populates='articles', cascade='all, delete')


class News(db.Model):
    __tablename__ = 'news'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(255))
    content: Mapped[str] = mapped_column(Text)
    last_update: Mapped[datetime] = mapped_column(DateTime)
    image_id: Mapped[int] = mapped_column(ForeignKey('image.id', ondelete='CASCADE'))

    image: Mapped['Image'] = relationship(back_populates='news', cascade="all, delete")



class TextbookChapter(db.Model):
    __tablename__ = 'textbook_chapter'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str] = mapped_column(String(255), nullable=True)

    textbook_paragraphs: Mapped[List['TextbookParagraph']] = relationship(back_populates='textbook_chapter', passive_deletes=True)

    def __repr__(self) -> str:
        return str(self.name)

    def __str__(self) -> str:
        return str(self.name)

class TextbookParagraph(SearchableMixin, db.Model):
    __tablename__ = 'textbook_paragraph'
    __searchable__ = ['content']

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    content: Mapped[str] = mapped_column(UnicodeText)
    textbook_chapter_id: Mapped[int] = mapped_column(ForeignKey('textbook_chapter.id', ondelete='SET NULL'), nullable=True)

    images: Mapped[List['TextbookParagraphImage']] = relationship(back_populates='textbook_paragraph', cascade='all, delete')
    textbook_chapter: Mapped['TextbookChapter'] = relationship(back_populates='textbook_paragraphs')

    def __repr__(self) -> str:
        return str(self.name)

    def __str__(self) -> str:
        return str(self.name)

class TextbookParagraphImage(db.Model):
    __tablename__ = 'textbook_paragraph_image'

    image_id: Mapped[int] = mapped_column(ForeignKey('image.id', ondelete='CASCADE'), primary_key=True)
    textbook_paragraph_id: Mapped[int] = mapped_column(ForeignKey('textbook_paragraph.id', ondelete='CASCADE'), primary_key=True)

    image: Mapped['Image'] = relationship(back_populates='textbook_paragraphs', cascade='all, delete')
    textbook_paragraph: Mapped['TextbookParagraph'] = relationship(back_populates='images')

db.event.listen(db.session, 'before_commit', SearchableMixin.before_commit)
db.event.listen(db.session, 'after_commit', SearchableMixin.after_commit)


