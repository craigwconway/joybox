from email.policy import default
from sqlalchemy import Boolean, Column, ForeignKey, Integer, Text
from sqlalchemy.orm import relationship

from app import db


class Sound(db.Model):
    id = Column(Integer, primary_key=True)
    name = Column(Text)
    order = Column(Integer, default=0)
    local_path = Column(Text)
    source_url = Column(Text)
    joycon_id = Column(Text, ForeignKey("joycon.id"))


class Joycon(db.Model):
    id = Column(Text, primary_key=True)  # rfid tag string
    name = Column(Text)
    repeat = Column(Boolean)
    shuffle = Column(Boolean)
    sounds = relationship("Sound", cascade="all, delete", order_by="Sound.order")
