import pytest

from django.test.client import Client

from news.models import News, Comment

from django.conf import settings
from datetime import datetime, timedelta
from django.utils import timezone


@pytest.fixture
def author(django_user_model):
    return django_user_model.objects.create(username='Автор')


@pytest.fixture
def not_author(django_user_model):
    return django_user_model.objects.create(username='Не автор')


@pytest.fixture
def author_client(author):
    client = Client()
    client.force_login(author)
    return client


@pytest.fixture
def not_author_client(not_author):
    client = Client()
    client.force_login(not_author)
    return client


@pytest.fixture
def news():
    news = News.objects.create(
        title='Заголовок новости',
        text='Текст новости',
        pk=1,
    )
    return news


@pytest.fixture
def create_multiple_news():
    today = datetime.today()
    all_news = [
        News(
            title=f'Новость {index}',
            text='Просто текст.',
            date=today - timedelta(days=index)
        )
        for index in range(settings.NEWS_COUNT_ON_HOME_PAGE + 1)
    ]
    return News.objects.bulk_create(all_news)


@pytest.fixture
def create_multiple_comments(news, author):
    now = timezone.now()
    for index in range(10):
        comment = Comment.objects.create(
            news=news, author=author, text=f'Текст {index}',
        )
        comment.created = now + timedelta(days=index)
        comment.save()


@pytest.fixture
def news_pk_for_args(news):
    return (news.pk,)


@pytest.fixture
def comment_pk_for_args(comment):
    return (comment.pk,)


@pytest.fixture
def comment(news, author):
    comment = Comment.objects.create(
        news=news,
        author=author,
        text='Текст комментария',
        pk=2,
    )
    return comment
