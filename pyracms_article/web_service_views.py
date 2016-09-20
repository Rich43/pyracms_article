from cornice import Service
from pyracms.lib.userlib import UserLib
from pyracms.web_service_views import valid_token

from .deform_schemas.article import EditArticleSchema
from .lib.articlelib import ArticleLib, PageNotFound, PageFound

article = Service(name='article', path='/api/article/item/{page_id}',
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
            request.errors.add('article', 'private', 'This page is private')
        else:
            return {'page': page.to_dict(), 'revision': revision.to_dict()}
    except PageNotFound:
        request.errors.add('article', 'not_found', 'Page Not Found')


@article.post(schema=EditArticleSchema, validators=valid_token)
def api_article_create_update(request):
    """
    Creates or Updates an article depending on if it exists or not.
    Accepts: display_name, article, summary, tags
    """
    page_id, display_name, article, summary, tags = quick_get_matchdict(request)
    user = u.show("admin")
    try:
        page = c.show_page(page_id)
        page.display_name = display_name
        c.update(request, page, article, summary, user, tags)
        return {"info": "updated"}
    except PageNotFound:
        c.create(request, page_id, display_name, article, summary,
                 user, tags)
        return {"info": "created"}


@article.put(schema=EditArticleSchema, validators=valid_token)
def api_article_create(request):
    """
    Creates an article.
    Accepts: display_name, article, summary, tags
    """
    page_id, display_name, article, summary, tags = quick_get_matchdict(request)
    user = u.show("admin")
    try:
        c.create(request, page_id, display_name, article, summary,
                 user, tags)
        return {"info": "created"}
    except PageFound:
        request.errors.add('article', 'found', 'A page already exists')


@article.patch(schema=EditArticleSchema, validators=valid_token)
def api_article_update(request):
    """
    Updates an article.
    Accepts: display_name, article, summary, tags
    """
    page_id, display_name, article, summary, tags = quick_get_matchdict(request)
    user = u.show("admin")
    try:
        page = c.show_page(page_id)
        page.display_name = display_name
        c.update(request, page, article, summary, user, tags)
        return {"info": "updated"}
    except PageNotFound:
        request.errors.add('article', 'not_found', 'Page not found')
