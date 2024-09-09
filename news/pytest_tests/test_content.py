import pytest
from django.urls import reverse
from django.conf import settings
from news.forms import CommentForm


@pytest.mark.django_db
@pytest.mark.parametrize(
    'client_type, has_form',
    [
        (pytest.lazy_fixture('client'), False),
        (pytest.lazy_fixture('author_client'), True),
    ]
)
@pytest.mark.parametrize(
    'name, args',
    [
        ('news:detail', pytest.lazy_fixture('news_pk_for_args')),
    ]
)
def test_form_visibility(client_type, name, args, has_form):
    """Тестируем видимость формы в зависимости от того,
    что клиент авторизирован или нет
    """
    response = client_type.get(reverse(name, args=args))
    if has_form:
        assert 'form' in response.context
        assert isinstance(response.context['form'], CommentForm)
    else:
        assert 'form' not in response.context


@pytest.mark.django_db
@pytest.mark.parametrize(
    'name, args, comments',
    (
        ('news:detail',
         pytest.lazy_fixture('news_pk_for_args'),
         pytest.lazy_fixture('create_multiple_comments'),
         ),
    )
)
def test_comments_order(client, name, args, comments):
    """Тестируем сортировку комментариев,
    от самых старых к самым свежим
    """
    response = client.get(reverse(name, args=args))
    news = response.context['news']
    all_comments = news.comment_set.all()
    all_timestamps = [comment.created for comment in all_comments]
    sorted_timestamps = sorted(all_timestamps)
    assert all_timestamps == sorted_timestamps


@pytest.mark.django_db
@pytest.mark.parametrize(
    'news',
    (pytest.lazy_fixture('create_multiple_news'),),

)
def test_news_count(client, news):
    """Тестируем количество новостей на главной странице,
    должно быть 10 новостей
    """
    response = client.get(reverse('news:home'))
    object_list = response.context['object_list']
    news_count = object_list.count()
    assert news_count == settings.NEWS_COUNT_ON_HOME_PAGE


@pytest.mark.django_db
@pytest.mark.parametrize(
    'news',
    (pytest.lazy_fixture('create_multiple_news'),),

)
def test_news_order(client, news):
    """Тестируем сортировку новостей,
    от самых свежих к самым старым
    """
    response = client.get(reverse('news:home'))
    object_list = response.context['object_list']
    all_dates = [news.date for news in object_list]
    sorted_dates = sorted(all_dates, reverse=True)
    assert all_dates == sorted_dates
