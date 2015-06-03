from ..models import (ArticleRevision, ArticlePage, ArticleRenderers, 
    ArticleTags, ArticleVotes)
from jinja2.filters import do_striptags
from pyracms.lib.helperlib import serialize_relation
from pyracms.lib.searchlib import SearchLib
from pyracms.lib.settingslib import SettingsLib
from pyracms.lib.taglib import TagLib, ARTICLE
from pyracms.lib.userlib import UserLib
from pyracms.lib.widgetlib import WidgetLib
from pyracms.models import DBSession
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm.exc import NoResultFound
import datetime
import json
import transaction

class RevisionNotFound(Exception):
    pass

class PageNotFound(Exception):
    pass

class PageFound(Exception):
    pass

class AlreadyVoted(Exception):
    pass

class ArticleLib():
    """
    A library to manage the article database.
    """

    def __init__(self):
        self.t = TagLib(ArticleTags, ARTICLE)
        self.s = SearchLib()
        
    def list(self): #@ReservedAssignment
        """
        List all the pages
        """
        pages = DBSession.query(ArticlePage)
        if not pages:
            raise PageNotFound
        return [(page.name, page.display_name or page.name) for page in pages]

    def update_article_index(self, request, page, revision, username):
        """
        Update search index
        """
        w = WidgetLib()
        rendered = ""
        try:
            rendered = do_striptags(w.render_article(page, revision.article))
        except:
            pass
        self.s.update_index(page.display_name, 
                            request.route_url("article_read", 
                                              page_id=page.name), rendered, 
                            self.t.get_tags(page), revision.created, 
                            "article", page.name, username)

    def switch_renderer(self, name):
        page = self.show_page(name)
        renderer_count = DBSession.query(ArticleRenderers).count()
        if page.renderer_id == renderer_count:
            page.renderer_id = 1
            return
        page.renderer_id += 1

    def create(self, request, name, display_name, article, summary, user,
               tags=''):
        """
        Add a new page
        Raise PageFound if page exists
        """
        try:
            self.show_page(name)
            raise PageFound
        except PageNotFound:
            pass
        s = SettingsLib()
        page = ArticlePage(name, display_name)
        revision = ArticleRevision(article, summary, user)
        page.revisions.append(revision)
        default_renderer = s.show_setting("DEFAULTRENDERER")
        page.renderer = DBSession.query(ArticleRenderers).filter_by(
                                                name=default_renderer).one()
        if s.has_setting("PYRACMS_FORUM"):
            from pyracms_forum.lib.boardlib import BoardLib
            page.thread_id = BoardLib().add_thread(name, display_name, "",
                                                   user, add_post=False).id
        if s.has_setting("PYRACMS_GALLERY"):
            from pyracms_gallery.lib.gallerylib import GalleryLib
            album = GalleryLib().create_album(name, display_name, user)
            page.album_id = album
        self.t.set_tags(page, tags)
        self.update_article_index(request, page, revision, user.name)
        DBSession.add(page)

    def update(self, request, page, article, summary, user, tags=''):
        """
        Update a page
        Raise PageNotFound if page does not exist
        """
        if not article:
            self.delete(page, user)
            return
        self.t.set_tags(page, tags)
        revision = ArticleRevision(article, summary, user)
        revision.page = page
        if not page.private:
            self.update_article_index(request, page, revision, user.name)
        DBSession.add(revision)

    def revert(self, request, page, revision, user):
        """
        Revert a page
        Raise PageNotFound if page does not exist
        """
        message = "Reverted revision %s" % revision.id
        self.update(request, page, revision.article, message, user)

    def delete(self, request, page):
        """
        Delete a page
        Raise PageNotFound if page does not exist
        """
        if page.thread_id != -1:
            from pyracms_forum.lib.boardlib import BoardLib
            BoardLib().delete_thread(page.thread_id)
        if page.album_id != -1:
            from pyracms_gallery.lib.gallerylib import GalleryLib
            GalleryLib().delete_album(page.album_id, request)
        DBSession.delete(page)
        self.s.delete_from_index(request.route_url("article_read", 
                                                   page_id=page.name))

    def set_private(self, request, name):
        """
        Flip private switch.
        Raise PageNotFound if page does not exist.
        """
        page = self.show_page(name)
        page.private = not page.private
        self.s.delete_from_index(request.route_url("article_read", 
                                                   page_id=page.name))

    def hide_display_name(self, name):
        """
        Flip hide display name switch.
        Raise PageNotFound if page does not exist.
        """
        page = self.show_page(name)
        page.hide_display_name = not page.hide_display_name

    def show_revision(self, page, revision, error=False):
        """
        Get revision objects.
        Raise RevisionNotFound if revision does not exist.
        """
        try:
            return page.revisions.filter_by(id=revision).one()
        except NoResultFound:
            if error:
                raise RevisionNotFound
            else:
                pass

    def show_page(self, name):
        """
        Get page objects.
        Raise PageNotFound if page does not exist.
        """
        try:
            page = DBSession.query(ArticlePage
                                   ).filter(ArticlePage.name.like(name)).one()
        except NoResultFound:
            raise PageNotFound
        return page

    def add_vote(self, db_obj, user, like):
        """
        Add a vote to the database
        """
        
        vote = ArticleVotes(user, like)
        vote.page = db_obj
        try:
            DBSession.add(vote)
            transaction.commit()
        except IntegrityError:
            transaction.abort()
            raise AlreadyVoted

    def to_json(self):
        pages = DBSession.query(ArticlePage)
        items = serialize_relation(pages)
        result = []
        for item in items:
            item['revisions'] = serialize_relation(self.show_page(item["name"]
                                                                  ).revisions)
            result.append(item)
        dthandler = (lambda obj: obj.isoformat() 
                     if isinstance(obj, datetime.datetime) else None)
        return json.dumps(result, default=dthandler)
    
    def from_json(self, request, data):
        u = UserLib()
        data = json.loads(data)
        def convert_date(date):
            if isinstance(date, str):
                date = date.split(".")[0]
            date_format = "%Y-%m-%dT%H:%M:%S"
            try:
                return datetime.datetime.strptime(date, date_format)
            except TypeError:
                return datetime.datetime(1900, 1, 1)
            except ValueError:
                return datetime.datetime(1900, 1, 1)
        # Convert the dates back
        for k, dummy in enumerate(data):
            data[k]['created'] = convert_date(data[k]['created'])
            for k2, dummy in enumerate(data[k]['revisions']):
                data[k]['revisions'][k2]['created'] = \
                            convert_date(data[k]['revisions'][k2]['created'])
        # Delete all articles
        for page in DBSession.query(ArticlePage):
            DBSession.delete(page)
            self.s.delete_from_index(request.route_url("article_read", 
                                                page_id=page.name))
        # Add articles back again
        for row in data:
            # Delete revisions and store in memory for later use
            revisions = row['revisions']
            del(row['revisions'])
            # Create page
            page = ArticlePage()
            for k, v in row.items():
                try:
                    setattr(page, k, v)
                except:
                    pass
            DBSession.add(page)
            page = self.show_page(row['name'])
            # Add revisions
            for row2 in revisions:
                revision = ArticleRevision()
                for k, v in row2.items():
                    try:
                        setattr(revision, k, v)
                    except:
                        pass
                page.revisions.append(revision)
                self.update_article_index(request, page, revision, 
                                          u.show_by_id(revision.user_id).name)