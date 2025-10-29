"""
Модуль тестирования контента и отображения приложения новостей.

Содержит тесты для проверки:
- Количества новостей на главной странице согласно настройкам
- Порядка сортировки новостей от новых к старым
- Порядка сортировки комментариев от старых к новым
- Доступности форм комментариев для авторизованных пользователей
- Корректности передачи данных в контекст шаблонов
"""
from datetime import datetime, timedelta  # type: ignore

from django.conf import settings  # type: ignore
from django.test import TestCase  # type: ignore
from django.urls import reverse  # type: ignore
from django.contrib.auth import get_user_model  # type: ignore
from django.utils import timezone  # type: ignore

from news.models import News, Comment  # type: ignore
from news.forms import CommentForm  # type: ignore

# Текущая дата.
today = datetime.today()

User = get_user_model()


class TestHomePage(TestCase):
    """
    Тестирование домашней страницы приложения новостей.

    Проверяет базовую функциональность главной страницы, включая
    ограничение количества отображаемых новостей и правильность их сортировки.
    """

    # Вынесем ссылку на домашнюю страницу в атрибуты класса.
    HOME_URL = reverse('news:home')

    @classmethod
    def setUpTestData(cls):
        """
        Подготавливает тестовые данные для домашней страницы.

        Создает количество новостей, превышающее лимит отображения,
        для проверки корректности пагинации.
        """
        News.objects.bulk_create(
            News(
                title=f'Новость {index}',
                text='Просто текст.',
                date=today - timedelta(days=index)
            )
            for index in range(settings.NEWS_COUNT_ON_HOME_PAGE + 1)
        )

    def test_news_count(self):
        """
        Проверяет ограничение количества новостей на главной странице.

        Убеждается, что количество отображаемых новостей не превышает
        значение NEWS_COUNT_ON_HOME_PAGE из настроек проекта.
        """
        # Загружаем главную страницу.
        response = self.client.get(self.HOME_URL)
        # Код ответа не проверяем, его уже проверили в тестах маршрутов.
        # Получаем список объектов из словаря контекста.
        object_list = response.context['object_list']
        # Определяем количество записей в списке.
        news_count = object_list.count()
        # Проверяем, что на странице именно 10 новостей.
        self.assertEqual(news_count, settings.NEWS_COUNT_ON_HOME_PAGE)

    def test_news_order(self):
        """
        Проверяет порядок сортировки новостей на главной странице.

        Убеждается, что новости отсортированы по дате в порядке убывания
        (сначала самые свежие, затем более старые).
        """
        response = self.client.get(self.HOME_URL)
        object_list = response.context['object_list']
        # Получаем даты новостей в том порядке, как они выведены на странице.
        all_dates = [news.date for news in object_list]
        # Сортируем полученный список по убыванию.
        sorted_dates = sorted(all_dates, reverse=True)
        # Проверяем, что исходный список был отсортирован правильно.
        self.assertEqual(all_dates, sorted_dates)


class TestDetailPage(TestCase):
    """
    Тестирование страницы детального просмотра новости.

    Проверяет функциональность страницы отдельной новости, включая
    отображение комментариев и доступность форм для разных пользователей.
    """

    @classmethod
    def setUpTestData(cls):
        """
        Подготавливает тестовые данные для страницы новости.

        Создает тестовую новость, пользователя и набор комментариев
        с разными датами создания для проверки сортировки.
        """
        cls.news = News.objects.create(
            title='Тестовая новость', text='Просто текст.'
        )
        # Сохраняем в переменную адрес страницы с новостью:
        cls.detail_url = reverse('news:detail', args=(cls.news.id,))
        cls.author = User.objects.create(username='Комментатор')
        # Запоминаем текущее время:
        now = timezone.now()
        # Создаём комментарии в цикле.
        for index in range(10):
            # Создаём объект и записываем его в переменную.
            comment = Comment.objects.create(
                news=cls.news, author=cls.author, text=f'Tекст {index}',
            )
            # Сразу после создания меняем время создания комментария.
            comment.created = now + timedelta(days=index)
            # И сохраняем эти изменения.
            comment.save()

    def test_comments_order(self):
        """
        Проверяет порядок сортировки комментариев на странице новости.

        Убеждается, что комментарии отсортированы по дате создания
        в порядке возрастания (сначала самые старые, затем новые).
        """
        response = self.client.get(self.detail_url)
        # Проверяем, что объект новости находится в словаре контекста
        # под ожидаемым именем - названием модели.
        self.assertIn('news', response.context)
        # Получаем объект новости.
        news = response.context['news']
        # Получаем все комментарии к новости.
        all_comments = news.comment_set.all()
        # Собираем временные метки всех комментариев.
        all_timestamps = [comment.created for comment in all_comments]
        # Сортируем временные метки, менять порядок сортировки не надо.
        sorted_timestamps = sorted(all_timestamps)
        # Проверяем, что временные метки отсортированы правильно.
        self.assertEqual(all_timestamps, sorted_timestamps)

    def test_anonymous_client_has_no_form(self):
        """
        Проверяет отсутствие формы комментария для анонимных пользователей.

        Убеждается, что анонимные пользователи не видят форму
        для добавления комментариев на странице новости.
        """
        response = self.client.get(self.detail_url)
        self.assertNotIn('form', response.context)

    def test_authorized_client_has_form(self):
        """
        Проверяет наличие формы комментария для авторизованных пользователей.

        Убеждается, что авторизованные пользователи видят форму
        для добавления комментариев правильного типа на странице новости.
        """
        # Авторизуем клиент при помощи ранее созданного пользователя.
        self.client.force_login(self.author)
        response = self.client.get(self.detail_url)
        self.assertIn('form', response.context)
        # Проверим, что объект формы соответствует нужному классу формы.
        self.assertIsInstance(response.context['form'], CommentForm)
