from pytest_django.asserts import assertRedirects, assertFormError

from django.urls import reverse

from news.models import Comment

import pytest

from news.forms import WARNING

from http import HTTPStatus


@pytest.mark.django_db
@pytest.mark.parametrize(
    'name, args',
    [
        ('news:detail', pytest.lazy_fixture('news_pk_for_args')),
    ]
)
def test_anonymous_user_cant_create_comment(
        client, comment_form_data, name, args):
    """Тестируем, что анонимный клиент не может создать комментарий"""
    url = reverse(name, args=args)
    client.post(url, data=comment_form_data)
    comments_count = Comment.objects.count()
    assert comments_count == 0


@pytest.mark.django_db
@pytest.mark.parametrize(
    'name, args',
    [
        ('news:detail', pytest.lazy_fixture('news_pk_for_args')),
    ]
)
def test_user_can_create_comment(author_client, comment_form_data, name, args):
    """Тестируем, что авторизированный клиент может создать комментарий"""
    url = reverse(name, args=args)
    response = author_client.post(url, data=comment_form_data)
    assertRedirects(response, f'{url}#comments')
    comments_count = Comment.objects.count()
    assert comments_count == 1
    comment = Comment.objects.get()
    assert comment.text == comment_form_data['text']


@pytest.mark.django_db
@pytest.mark.parametrize(
    'name, args, bad_words',
    [
        (
            'news:detail',
            pytest.lazy_fixture('news_pk_for_args'),
            pytest.lazy_fixture('bad_words_data')
        ),
    ]
)
def test_user_cant_use_bad_words(author_client, name, args, bad_words):
    """Тестируем, что комментарий с запрещенными словами не будет сохранен
    и сработает предупреждение формы
    """
    url = reverse(name, args=args)
    response = author_client.post(url, data=bad_words)
    assertFormError(
        response,
        form='form',
        field='text',
        errors=WARNING
    )
    comments_count = Comment.objects.count()
    assert comments_count == 0


def test_author_can_delete_comment(
        author_client, comment_pk_for_args, news_pk_for_args
):
    """Тестируем, что автор может удалить свой комментарий"""
    delete_url = reverse('news:delete', args=comment_pk_for_args)
    news_url = reverse('news:detail', args=news_pk_for_args)
    response = author_client.post(delete_url)
    assertRedirects(response, f'{news_url}#comments')
    comments_count = Comment.objects.count()
    assert comments_count == 0


@pytest.mark.django_db
def test_user_cant_delete_comment_of_another_user(
    not_author_client, comment_pk_for_args
):
    """Тестируем, что пользователь не может удалить чужой комментарий"""
    delete_url = reverse('news:delete', args=comment_pk_for_args)
    response = not_author_client.post(delete_url)
    assert response.status_code == HTTPStatus.NOT_FOUND
    comments_count = Comment.objects.count()
    assert comments_count == 1


def test_author_can_edit_comment(
        author_client, comment_pk_for_args, comment_form_data,
        news_pk_for_args, comment
):
    """Тестируем, что автор может редактировать комментарий"""
    edit_url = reverse('news:edit', args=comment_pk_for_args)
    comment_form_data['text'] = 'Отредактированный комментарий'
    response = author_client.post(edit_url, data=comment_form_data)
    news_url = reverse('news:detail', args=news_pk_for_args)
    assertRedirects(response, f'{news_url}#comments')
    comment.refresh_from_db()
    assert comment.text == 'Отредактированный комментарий'
