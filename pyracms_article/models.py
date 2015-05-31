from datetime import datetime
from pyracms.models import Base, User
from sqlalchemy.orm import relationship
from sqlalchemy.schema import Column, ForeignKey, UniqueConstraint
from sqlalchemy.sql.expression import desc
from sqlalchemy.types import Integer, Unicode, UnicodeText, DateTime, Boolean

class ArticleTags(Base):
    __tablename__ = 'articletags'
    __table_args__ = {'mysql_engine': 'InnoDB', 'mysql_charset': 'utf8'}

    id = Column(Integer, primary_key=True)
    name = Column(Unicode(128), index=True, nullable=False)
    page_id = Column(Integer, ForeignKey('articlepage.id'))
    page = relationship("ArticlePage")

    def __init__(self, name):
        self.name = name

class ArticleRevision(Base):
    __tablename__ = 'articlerevision'
    __table_args__ = {'mysql_engine': 'InnoDB', 'mysql_charset': 'utf8'}

    id = Column(Integer, primary_key=True)
    page_id = Column(Integer, ForeignKey('articlepage.id'), nullable=False)
    article = Column(UnicodeText, default='')
    summary = Column(Unicode(128), index=True, nullable=False)
    user_id = Column(Integer, ForeignKey('user.id'), nullable=False)
    user = relationship(User)
    page = relationship("ArticlePage")
    created = Column(DateTime, default=datetime.now)

    def __init__(self, article="", summary="", user=None):
        self.article = article
        self.summary = summary
        if user:
            self.user = user

class ArticleRenderers(Base):
    __tablename__ = 'articlerenderers'
    __table_args__ = {'mysql_engine': 'InnoDB', 'mysql_charset': 'utf8'}

    id = Column(Integer, primary_key=True)
    name = Column(Unicode(128), index=True, unique=True, nullable=False)

    def __init__(self, name):
        self.name = name

class ArticlePage(Base):
    __tablename__ = 'articlepage'
    __table_args__ = {'mysql_engine': 'InnoDB', 'mysql_charset': 'utf8'}

    id = Column(Integer, primary_key=True)
    name = Column(Unicode(128), index=True, unique=True, nullable=False)
    display_name = Column(Unicode(128), index=True, nullable=False)
    hide_display_name = Column(Boolean, default=False, index=True)
    created = Column(DateTime, default=datetime.now)
    private = Column(Boolean, default=False, index=True)
    view_count = Column(Integer, default=0, index=True)
    thread_id = Column(Integer, nullable=False, default=-1)
    album_id = Column(Integer, nullable=False, default=-1)
    renderer_id = Column(Integer, ForeignKey('articlerenderers.id'),
                         nullable=False, default=1)
    revisions = relationship(ArticleRevision,
                             cascade="all, delete, delete-orphan",
                             lazy="dynamic",
                             order_by=desc(ArticleRevision.created))
    tags = relationship(ArticleTags, cascade="all, delete, delete-orphan")
    votes = relationship("ArticleVotes", lazy="dynamic", 
                         cascade="all, delete, delete-orphan")
    renderer = relationship(ArticleRenderers)

    def __init__(self, name="", display_name=""):
        self.name = name
        self.display_name = display_name

class ArticleVotes(Base):
    __tablename__ = 'articlevotes'
    __table_args__ = (UniqueConstraint('user_id', 'page_id'),
                      {'mysql_engine': 'InnoDB', 'mysql_charset': 'utf8'})

    id = Column(Integer, primary_key=True)
    page_id = Column(Integer, ForeignKey('articlepage.id'))
    page = relationship(ArticlePage)
    user_id = Column(Integer, ForeignKey('user.id'), nullable=False)
    user = relationship("User")
    like = Column(Boolean, nullable=False, index=True)

    def __init__(self, user, like):
        self.user = user
        self.like = like
