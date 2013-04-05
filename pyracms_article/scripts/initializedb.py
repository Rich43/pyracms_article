from ..models import ArticlePage, ArticleVotes, ArticleRevision # @UnusedImports
from ..models import ArticleRenderers # @UnusedImports
from ..models import ArticleTags # @UnusedImports
from pyracms.factory import RootFactory
from pyracms.lib.menulib import MenuLib
from pyracms.lib.userlib import UserLib
from pyracms.models import DBSession, Base, Menu, MenuGroup
from pyramid.paster import get_appsettings, setup_logging
from pyramid.security import Allow, Everyone, Authenticated
from sqlalchemy import engine_from_config
import os
import sys
import transaction

def usage(argv):
    cmd = os.path.basename(argv[0])
    print('usage: %s <config_uri>\n'
          '(example: "%s development.ini")' % (cmd, cmd)) 
    sys.exit(1)

def main(argv=sys.argv):
    if len(argv) != 2:
        usage(argv)
    config_uri = argv[1]
    setup_logging(config_uri)
    settings = get_appsettings(config_uri)
    engine = engine_from_config(settings, 'sqlalchemy.')
    DBSession.configure(bind=engine)
    Base.metadata.create_all(engine)
    with transaction.manager:
        # Add Groups
        u = UserLib()
        admin_user = u.show("admin")
        u.create_group("article", "Ability to Add, Edit, Delete, " +
                       "Revert and Protect Articles.", [admin_user])
    
        # Default ACL
        acl = RootFactory(session=DBSession)
        acl.__acl__.append((Allow, "group:admin", "switch_renderer"))
        acl.__acl__.append((Allow, "group:admin", "set_private"))
        acl.__acl__.append((Allow, Authenticated, "article_list_revisions"))
        acl.__acl__.append((Allow, Everyone, "article_view"))
        acl.__acl__.append((Allow, Everyone, "article_list"))
        acl.__acl__.append((Allow, "group:article", "group:article"))
        acl.__acl__.append((Allow, "group:article", "article_view"))
        acl.__acl__.append((Allow, "group:article", "article_list"))
        acl.__acl__.append((Allow, "group:article", "article_create"))
        acl.__acl__.append((Allow, "group:article", "article_update"))
        acl.__acl__.append((Allow, "group:article", "article_delete"))
        acl.__acl__.append((Allow, "group:article", "article_revert"))

        # Add Menu Items
        m = MenuLib()
        group = m.show_group("main_menu")
        DBSession.add(Menu("Articles", "/article/list", 2, group, Everyone))
        
        group = m.show_group("admin_area")
        DBSession.add(Menu("Backup Articles", "/userarea_admin/backup_articles",
                           8, group, 'backup'))
        DBSession.add(Menu("Restore Articles", 
                           "/userarea_admin/restore_articles", 
                           9, group, 'backup'))
        
        group = MenuGroup("article_not_revision")
        DBSession.add(Menu("Edit", "/article/update/%(page_id)s", 
                           1, group, 'article_update'))
        DBSession.add(Menu("Delete", "/article/delete/%(page_id)s", 
                           2, group, 'article_delete'))
        DBSession.add(Menu("Switch Renderer [%(renderer)s]",
                           "/article/switch_renderer/%(page_id)s", 
                           3, group, 'switch_renderer'))
        DBSession.add(Menu("Make %(private)s",
                           "/article/set_private/%(page_id)s", 
                           4, group, 'set_private'))
        DBSession.add(Menu("Vote Up (%(up_count)s)", 
                           "/vote/article/%(page_id)s/True", 5, 
                           group, 'vote'))
        DBSession.add(Menu("Vote Down (%(down_count)s)", 
                           "/vote/article/%(page_id)s/False", 6, 
                           group, 'vote'))
        DBSession.add(Menu("List Revisions",
                           "/article/list_revisions/%(page_id)s",
                           7, group, 'article_list_revisions'))
        
        group = MenuGroup("article_revision")
        DBSession.add(Menu("List Revisions",
                           "/article/list_revisions/%(page_id)s", 1, group))
        DBSession.add(Menu("Revert",
                           "/article/revert/%(page_id)s/%(revision)s", 
                           2, group))
        
        # Add Renderers
        DBSession.add(ArticleRenderers("HTML"))
        DBSession.add(ArticleRenderers("BBCODE"))
        DBSession.add(ArticleRenderers("RESTRUCTUREDTEXT"))
        DBSession.add(ArticleRenderers("MARKDOWN"))