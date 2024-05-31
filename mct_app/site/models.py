from datetime import datetime
from typing import List, Optional


from sqlalchemy import DateTime, Integer, String, ForeignKey, UnicodeText, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship


from mct_app import db

class Image(db.Model):
    __tablename__ = "image"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    filename: Mapped[str] = mapped_column(String)
    absolute_path: Mapped[str] = mapped_column(String(255))
    relative_path: Mapped[str] = mapped_column(String(255))

    news: Mapped['News'] = relationship(back_populates='image')
    article_card: Mapped['ArticleCard'] = relationship(back_populates='image')
    articles: Mapped[List['ArticleImage']] = relationship(back_populates='image')


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


class Article(db.Model):
    __tablename__ = 'article'

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


