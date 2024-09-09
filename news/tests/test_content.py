from django.conf import settings
from django.test import TestCase
from django.urls import reverse
# Импортируем функцию для получения модели пользователя
from django.contrib.auth import get_user_model
# Импортируем класс, который определяет время и ЧАСОВОЙ ПОЯС
from django.utils import timezone

from news.models import News, Comment
from news.forms import CommentForm

from datetime import datetime, timedelta

User = get_user_model()


class TestHomepage(TestCase):
    # Вынесем ссылку на домашнюю страницу в атрибуты класса.
    HOME_URL = reverse('news:home')

    @classmethod
    def setUpTestData(cls) -> None:
        """Создаем 11 новостей, на 1 больше чем должно быть на странице"""
        # Вычисляем текущую дату, даты нужны
        # для тестирования сортировки новостей по датам
        today = datetime.today()
        all_news = [
            News(
                title=f'Новость {index}',
                text='Просто текст.',
                # Для каждой новости уменьшаем дату на index дней от today,
                # где index - счётчик цикла.
                date=today - timedelta(days=index)
            )
            for index in range(settings.NEWS_COUNT_ON_HOME_PAGE + 1)
        ]
        News.objects.bulk_create(all_news)

    def test_news_count(self):
        # Проверяем количество новостей на главной странице, должно быть 10
        # Загружаем главную страницу
        response = self.client.get(self.HOME_URL)
        # Код ответа не проверяем, его уже проверили в тестах маршрутов.
        # Получаем список объектов из словаря контекста.
        object_list = response.context['object_list']
        # Определяем количество записей в списке.
        news_count = object_list.count()
        self.assertEqual(news_count, settings.NEWS_COUNT_ON_HOME_PAGE)

    def test_news_order(self):
        # Тестируем порядок вывода (сортировку) новостей.
        # от самых свежих к самым старым.
        response = self.client.get(self.HOME_URL)
        object_list = response.context['object_list']
        # Получаем даты новостей в том порядке, как они выведены на странице.
        all_dates = [news.date for news in object_list]
        # Сортируем полученный список по убыванию.
        sorted_dates = sorted(all_dates, reverse=True)
        # Проверяем, что исходный список был отсортирован правильно.
        self.assertEqual(all_dates, sorted_dates)


class TestDetailPage(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.news = News.objects.create(
            title='Тестовая новость', text='Просто текст.'
        )
        # Сохраняем в переменную адрес страницы с новостью:
        cls.detail_url = reverse('news:detail', args=(cls.news.id,))
        cls.author = User.objects.create(username='Комментатор')
        # Запоминаем текущее время с часовым поясом:
        now = timezone.now()
        # Создаем комментарии в цикле.
        for index in range(10):
            # Создаем объект и записываем его в переменную.
            comment = Comment.objects.create(
                news=cls.news, author=cls.author, text=f'Текст {index}',
            )
            # Сразу после создания меняем время создания комментария.
            comment.created = now + timedelta(days=index)
            # И сохраняем эти изменения.
            comment.save()

    def test_comments_order(self):
        # Тестируем порядок вывода комментариев,
        # он отличается от сортировки новостей,
        # здесь от "старых к новым"

        response = self.client.get(self.detail_url)
        # Проверяем, что объект новости находится в словаре контекста
        # под ожидаемым именем - названием модели.
        self.assertIn('news', response.context)
        # Получаем объект новости.
        news = response.context['news']
        # Получаем все комментарии к новости, comments_set.all() подсмотрели
        #  в шаблоне вывода комментариев (detail.html)
        all_comments = news.comment_set.all()
        # Собираем временные метки всех новостей.
        all_timestamps = [comment.created for comment in all_comments]
        # Сортируем временные метки, менять порядок сортировки не надо.
        sorted_timestamps = sorted(all_timestamps)
        # Проверяем, что временные метки остортированы правильно.
        self.assertEqual(all_timestamps, sorted_timestamps)

    def test_anonymos_client_has_no_form(self):
        # Тестируем отсутствие формы у анонимного пользователя
        response = self.client.get(self.detail_url)
        self.assertNotIn('form', response.context)

    def test_authorized_client_has_form(self):
        # Авторизуем клиент при помощи ранее созданного пользователя.
        self.client.force_login(self.author)
        response = self.client.get(self.detail_url)
        self.assertIn('form', response.context)
        # Проверим, что объект формы соответствует нужному классу формы.
        self.assertIsInstance(response.context['form'], CommentForm)
