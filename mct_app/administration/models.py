from sqlalchemy import Integer, String
from mct_app import db
from sqlalchemy.orm import Mapped, mapped_column

class BannedIPs(db.Model):
    __tablename__ = 'banned_ips'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    banned_ip: Mapped[str] = mapped_column(String(15), nullable=False)