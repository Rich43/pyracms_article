from .views import article_read
def includeme(config):
    """ Activate the forum; usually called via
    ``config.include('pyracms_forum')`` instead of being invoked
    directly. """
    config.include('pyramid_jinja2')
    config.add_jinja2_search_path("pyracms_article:templates")
    
    # Userarea Admin Routes
    config.add_route('userarea_admin_backup_articles',
                     '/userarea_admin/backup_articles')
    config.add_route('userarea_admin_restore_articles',
                     '/userarea_admin/restore_articles')
    
    # Article Routes
    if config.get_settings().get("enable_pyracms_article_home"):
        config.add_view(article_read, route_name='home', 
                        renderer='article/article.jinja2', 
                        permission='article_view')
        config.add_route('home', '/')
    config.add_route('article_read', '/article/item/{page_id}')
    config.add_route('article_read_revision',
                     '/article/item/{page_id}/{revision}')
    config.add_route('article_list', '/article/list')
    config.add_route('article_revert',
                     '/article/revert/{page_id}/{revision}')
    config.add_route('article_delete', '/article/delete/{page_id}')
    config.add_route('article_create', '/article/create/{page_id}')
    config.add_route('article_update', '/article/update/{page_id}')
    config.add_route('article_list_revisions',
                     '/article/list_revisions/{page_id}')
    config.add_route('article_switch_renderer',
                     '/article/switch_renderer/{page_id}')
    config.add_route('article_set_private', '/article/set_private/{page_id}')
    config.add_route('article_hide_display_name',
                     '/article/hide_display_name/{page_id}')
    config.add_route('article_add_vote', '/vote/article/{vote_id}/{like}')
    
    config.scan("pyracms_article.views")
    config.scan("pyracms_article.web_service_views")
