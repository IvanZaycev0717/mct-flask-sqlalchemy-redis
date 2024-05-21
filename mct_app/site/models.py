from sqlalchemy import DateTime, Integer, String, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from mct_app import db

class Image(db.Model):
    __tablename__ = "image"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    absolute_path: Mapped[str] = mapped_column(String(255))
    relative_path: Mapped[str] = mapped_column(String(255))

    news: Mapped['News'] = relationship(back_populates='image')

class Article(db.Model):
    __tablename__ = 'article'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

class News(db.Model):
    __tablename__ = 'news'
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(255))
    content: Mapped[str] = mapped_column(String)
    last_update: Mapped[DateTime] = mapped_column(DateTime)
    image_id: Mapped[int] = mapped_column(ForeignKey('image.id', ondelete='CASCADE'))

    image: Mapped['Image'] = relationship(back_populates='news', cascade="all, delete")


