# -*- coding: utf-8 -*-

from tornado.web import HTTPError

from doodle.config import CONFIG
from doodle.core.models.article import Article, ArticleHitCount
from doodle.core.models.comment import ArticleComments

from ..base_handler import UserHandler


class ArticleHandler(UserHandler):
    def get(self, url, date, _from_head=False):
        article = Article.get_by_url(url)
        if not article:
            redirect_url = Article.search(date, url)
            if redirect_url:
                self.redirect(CONFIG.BLOG_HOME_RELATIVE_PATH + redirect_url, permanent=True)
                return
            else:
                raise HTTPError(404)

        if not (article.public or self.is_admin):
            raise HTTPError(404)

        previous_article, next_article = article.get_nearby_articles()
        if _from_head or self.request.headers.get('If-None-Match') or self.is_spider:
            hit_count = ArticleHitCount.get(article.id)
        else:
            hit_count = ArticleHitCount.increase(article.id)
        replies = ArticleComments.get_comment_count_of_article(article.id)

        self.set_cache(CONFIG.DEFAULT_CACHE_TIME, is_public=article.public)
        self.render('web/article.html', {
            'title': article.title,
            'page': 'article',
            'article': article,
            'previous_article': previous_article,
            'next_article': next_article,
            'hits': hit_count,
            'replies': replies
        })

    def head(self, url, date):
        self.get(url, date, _from_head=True)


class ArticleIDHandler(UserHandler):
    def get(self, article_id):
        article_id = int(article_id)
        if not article_id:
            raise HTTPError(404)

        article = Article.get_by_id(article_id)
        if article:
            if not article.public:
                self.set_cache(is_public=False)
                if not self.is_admin:
                    raise HTTPError(404)
            self.redirect(CONFIG.BLOG_HOME_RELATIVE_PATH + article.url, permanent=True)
        else:
            raise HTTPError(404)
