from sqlalchemy import DateTime, Integer, String, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from mct_app import db
from mct_app.auth.models import User

class Image(db.Model):
    __tablename__ = "image"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(45))
    url: Mapped[str] = mapped_column(String(255))
    path: Mapped[str] = mapped_column(String(255))
    path_id: Mapped[int] = mapped_column(Integer)

class Article(db.Model):
    __tablename__ = 'article'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

