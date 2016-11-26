from cornice import Service
from cornice.validators import colander_body_validator

from pyracms.lib.userlib import UserLib
from pyracms.web_service_views import valid_token, valid_permission, APP_JSON

from .deform_schemas.article import EditArticleSchema
from .lib.articlelib import ArticleLib, PageNotFound, PageFound

article = Service(name='api_article', path='/api/article/item/{page_id}',
                  description="Create, read, update, delete articles")
c = ArticleLib()
u = UserLib()


def quick_get_matchdict(request):
    page_id = request.matchdict.get('page_id') or "Front_Page"
    display_name = request.json_body.get('display_name') or ""
    article = request.json_body.get('article') or ""
    summary = request.json_body.get('summery') or ""
    tags = request.json_body.get('tags') or ""
    return page_id, display_name, article, summary, tags


def check_owner(request, page_id):
    page = c.show_page(page_id)
    if (valid_permission(request, 'article_mod') or
        page.user == request.validated['user_db']):
        return True
    else:
        request.errors.add('body', 'access_denied', 'Access denied')
    return False

@article.get()
def api_article_read(request):
    """Gets an article from the database."""
    page_id = request.matchdict.get('page_id') or "Front_Page"
    revision_id = request.matchdict.get('revision')
    try:
        page = c.show_page(page_id)
        if revision_id:
            revision = c.show_revision(page, revision_id)
        else:
            revision = page.revisions[0]
        if page.private:
            request.errors.add('body', 'private', 'This page is private')
        else:
            # TODO: Iterate revisions and list them
            return {'page': page.to_dict(), 'revision': revision.to_dict()}
    except PageNotFound:
        request.errors.add('querystring', 'not_found', 'Page Not Found')


@article.put(schema=EditArticleSchema, content_type=APP_JSON,
             validators=(valid_token, colander_body_validator))
def api_article_create(request):
    """
    Creates an article.
    Accepts: display_name, article, summary, tags
    """
    # TODO: Create a BBThread
    # TODO: Create a Gallery
    if not valid_permission(request, "article_create"):
        request.errors.add('body', 'access_denied', 'Access denied')
        return
    page_id, display_name, article, summary, tags = quick_get_matchdict(request)
    user = request.validated['user_db']
    try:
        c.create(request, page_id, display_name, article, summary,
                 user, tags)
        return {"status": "created"}
    except PageFound:
        request.errors.add('querystring', 'found', 'A page already exists')


@article.patch(schema=EditArticleSchema, content_type=APP_JSON,
               validators=(valid_token, colander_body_validator))
def api_article_update(request):
    """
    Updates an article.
    Accepts: display_name, article, summary, tags
    """
    if not valid_permission(request, "article_update"):
        request.errors.add('body', 'access_denied', 'Access denied')
        return
    page_id, display_name, article, summary, tags = quick_get_matchdict(request)
    check_owner(request, page_id)
    user = request.validated['user_db']
    try:
        page = c.show_page(page_id)
        page.display_name = display_name
        c.update(request, page, article, summary, user, tags)
        return {"status": "updated"}
    except PageNotFound:
        request.errors.add('querystring', 'not_found', 'Page not found')


@article.delete(validators=valid_token)
def api_article_delete(request):
    if not valid_permission(request, "article_delete"):
        request.errors.add('body', 'access_denied', 'Access denied')
        return
    page_id = request.matchdict.get('page_id')
    check_owner(request, page_id)
    try:
        c.delete(request, c.show_page(page_id))
        return {"status": "deleted"}
    except PageNotFound:
        request.errors.add('querystring', 'not_found', 'Page Not Found')


article_list = Service(name='api_article_list', path='/api/article/list')
@article_list.get()
def api_article_list(request):
    return c.list()
