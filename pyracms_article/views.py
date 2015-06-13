from pyracms.deform_schemas.userarea_admin import RestoreBackupSchema
from pyracms.lib.helperlib import redirect, get_username, rapid_deform
from pyracms.lib.settingslib import SettingsLib
from pyracms.lib.taglib import TagLib, ARTICLE
from pyracms.lib.userlib import UserLib
from pyracms.views import ERROR, INFO
from pyramid.httpexceptions import HTTPForbidden
from pyramid.security import has_permission
from pyramid.view import view_config

from pyracms_article.deform_schemas.article import EditArticleSchema
from pyracms_article.lib.articlelib import (ArticleLib, PageNotFound,
                                            AlreadyVoted)
from pyracms_article.models import ArticleTags

u = UserLib()
s = SettingsLib()

def check_owner(context, request):
    page_id = request.matchdict.get('page_id')
    g = ArticleLib()
    page = g.show_page(page_id)
    if (has_permission('article_mod', context, request) or
        page.user == u.show(get_username(request))):
        return True
    else:
        raise HTTPForbidden

@view_config(route_name='article_read', renderer='article/article.jinja2',
             permission='article_view')
@view_config(route_name='article_read_revision',
             renderer='article/article.jinja2', permission='article_view')
def article_read(context, request):
    """
    Display an article
    """
    c = ArticleLib()
    result = {}
    page_id = request.matchdict.get('page_id') or "Front_Page"
    revision_id = request.matchdict.get('revision')
    try:
        page = c.show_page(page_id)
        revision = c.show_revision(page, revision_id)
        if page.private and not has_permission("set_private", context,
                                               request):
            raise HTTPForbidden
        else:
            result.update({'page': page, 'revision': revision, "thread_enabled": False})
            if request.query_string.startswith("comments") and page.thread_id != -1:
                from pyracms_forum.views import get_thread
                result.update(get_thread(context, request, page.thread_id))
                result.update({"thread_enabled": True})
            return result
    except PageNotFound:
        return redirect(request, "article_create", page_id=page_id)


@view_config(route_name='article_delete', permission='article_delete')
def article_delete(context, request):
    """
    Delete an article
    """
    check_owner(context, request)
    c = ArticleLib()
    page_id = request.matchdict.get('page_id')
    try:
        c.delete(request, c.show_page(page_id))
        request.session.flash(s.show_setting("INFO_DELETED")
                              % page_id, INFO)
        return redirect(request, "article_list")
    except PageNotFound:
        request.session.flash(s.show_setting("ERROR_NOT_FOUND")
                              % page_id, ERROR)
        return redirect(request, "article_list")


@view_config(route_name='article_list', permission='article_list',
             renderer='article/article_list.jinja2')
def article_list(context, request):
    """
    Show a list of articles
    """
    c = ArticleLib()
    return {'pages': c.list()}


@view_config(route_name='article_list_revisions',
             permission='article_list_revisions',
             renderer='article/article_list_revisions.jinja2')
def article_list_revisions(context, request):
    """
    Show a list of article revisions, every time a change is made, 
    a revision is added
    """
    c = ArticleLib()
    page_id = request.matchdict.get('page_id')
    try:
        page = c.show_page(page_id)
    except PageNotFound:
        request.session.flash(s.show_setting("ERROR_NOT_FOUND")
                              % page_id, ERROR)
        return redirect(request, "article_list")
    return {'page': page}


@view_config(route_name='article_update', permission='article_update',
             renderer='article/article_update.jinja2')
def article_update(context, request):
    """
    Display edit article form
    """
    check_owner(context, request)
    c = ArticleLib()

    def article_update_submit(context, request, deserialized, bind_params):
        """
        Add a article revision to the database
        """
        page = bind_params.get("page")
        name = request.matchdict.get("page_id")
        article = deserialized.get("article")
        summary = deserialized.get("summary")
        tags = deserialized.get("tags")
        page.display_name = deserialized.get("display_name")
        c.update(request, page, article, summary,
                 u.show(get_username(request)), tags)
        return redirect(request, "article_read", page_id=name)

    page_id = request.matchdict.get('page_id')
    page = c.show_page(page_id)
    revision = c.show_revision(page, request.matchdict.get('revision'))
    t = TagLib(ArticleTags, ARTICLE)
    display_name = page_id
    article = ""
    tags = ""
    if page:
        display_name = page.display_name
        article = page.revisions[0].article
        tags = t.get_tags(page)
    return rapid_deform(context, request, EditArticleSchema,
                        article_update_submit, page=page,
                        revision=revision, article=article,
                        display_name=display_name, tags=tags)


@view_config(route_name='article_create', permission='article_create',
             renderer='article/article_update.jinja2')
def article_create(context, request):
    """
    Display create a new article form
    """
    c = ArticleLib()

    def article_create_submit(context, request, deserialized, bind_params):
        """
        Save new article to the database
        """
        name = request.matchdict.get("page_id")
        display_name = deserialized.get("display_name")
        article = deserialized.get("article")
        summary = deserialized.get("summary")
        tags = deserialized.get("tags")
        c.create(request, name, display_name, article, summary,
                 u.show(get_username(request)), tags)
        return redirect(request, "article_read", page_id=name)

    return rapid_deform(context, request, EditArticleSchema,
                        article_create_submit,
                        page_id=request.matchdict.get("page_id"))


@view_config(route_name='article_revert', permission='article_revert')
def article_revert(context, request):
    """
    Revert an old revision, basically makes a new revision with old contents
    """
    check_owner(context, request)
    c = ArticleLib()
    matchdict_get = request.matchdict.get
    try:
        page = c.show_page(matchdict_get('page_id'))
        c.revert(request, page,
                 c.show_revision(page, matchdict_get('revision')),
                 u.show(get_username(request)))
        request.session.flash(s.show_setting("INFO_REVERT")
                              % page.name, INFO)
        return redirect(request, "article_read", page_id=page.name)
    except PageNotFound:
        request.session.flash(s.show_setting("ERROR_NOT_FOUND")
                              % matchdict_get('page_id'), ERROR)
        return redirect(request, "article_list")


@view_config(route_name='article_switch_renderer', permission='switch_renderer')
def article_switch_renderer(context, request):
    """
    Use another rendering engine for the page
    """
    c = ArticleLib()
    page_id = request.matchdict.get('page_id')
    c.switch_renderer(page_id)
    return redirect(request, "article_read", page_id=page_id)


@view_config(route_name='article_set_private', permission='set_private')
def article_set_private(context, request):
    """
    Make page private
    """
    c = ArticleLib()
    page_id = request.matchdict.get('page_id')
    c.set_private(page_id)
    return redirect(request, "article_read", page_id=page_id)

@view_config(route_name='article_hide_display_name', permission='set_private')
def article_hide_display_name(context, request):
    """
    Hide display name header
    """
    c = ArticleLib()
    page_id = request.matchdict.get('page_id')
    c.hide_display_name(page_id)
    return redirect(request, "article_read", page_id=page_id)

@view_config(route_name='article_add_vote', permission='vote')
def article_add_vote(context, request):
    """
    Add a vote to an article
    """
    vote_id = request.matchdict.get('vote_id')
    like = request.matchdict.get('like').lower() == "true"
    a = ArticleLib()
    article = a.show_page(vote_id)
    try:
        a.add_vote(article, u.show(get_username(request)), like)
        request.session.flash(s.show_setting("INFO_VOTE"), INFO)
    except AlreadyVoted:
        request.session.flash(s.show_setting("ERROR_VOTE"), ERROR)
    return redirect(request, "article_read", page_id=vote_id)


@view_config(route_name='userarea_admin_backup_articles', permission='backup')
def userarea_admin_backup_articles(context, request):
    a = ArticleLib()
    res = request.response
    res.content_type = "application/json"
    res.text = str(a.to_json())
    return res


@view_config(route_name='userarea_admin_restore_articles', permission='backup',
             renderer='deform.jinja2')
def userarea_admin_restore_articles(context, request):
    def restore_backup_submit(context, request, deserialized, bind_params):
        a = ArticleLib()
        a.from_json(request, deserialized['restore_backup_json_file']
        ['fp'].read().decode())
        return redirect(request, "article_list")

    result = rapid_deform(context, request, RestoreBackupSchema,
                          restore_backup_submit)
    if isinstance(result, dict):
        message = "Restore Articles from JSON File"
        result.update({"title": message, "header": message})
    return result
