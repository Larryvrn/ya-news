"""Фикстуры для тестов приложения news.

Общие данные и настройки для всех тестов pytest.
"""
import pytest

from datetime import datetime, timedelta  # type: ignore
# Импортируем класс клиента.
from django.test.client import Client  # type: ignore
from django.conf import settings  # type: ignore
from django.utils import timezone  # type: ignore

# Импортируем модель заметки, чтобы создать экземпляр.
from news.models import News, Comment

today = datetime.today()


@pytest.fixture
def author(django_user_model):
    """Используем фикстуру для модели пользователей и создаем автора."""
    return django_user_model.objects.create(username='Лев Толстой')


@pytest.fixture
def not_author(django_user_model):
    """Используем фикстуру для модели пользователей и создаем НЕ_автора."""
    return django_user_model.objects.create(username='Читатель простой')


@pytest.fixture
def author_client(author):
    """Вызоваем фикстуру автора и создаём новый экземпляр клиента, логиним."""
    client = Client()
    client.force_login(author)  # логиним автора в клиенте
    return client


@pytest.fixture
def not_author_client(not_author):
    """Фикстура логинит обычного пользователя."""
    client = Client()
    client.force_login(not_author)
    return client


@pytest.fixture
def news():
    """Фикстура создаёт новость."""
    news = News.objects.create(
        title='Заголовок',
        text='Текст',
    )
    return news


@pytest.fixture
def comment(author, news):
    """Фикстура создаёт комментарий Автора к новостию."""
    comment = Comment.objects.create(
        news=news,
        author=author,
        text='Текст комментария',
    )
    return comment


@pytest.fixture
def create_news():
    """Фикстура создаёт новости для тестов главной страницы."""
    from news.models import News  # Импортируем здесь, если нужно
    News.objects.bulk_create(
        News(
            title=f'Новость {index}',
            text='Просто текст.',
            date=today - timedelta(days=index)
        )
        for index in range(settings.NEWS_COUNT_ON_HOME_PAGE + 1)
    )


@pytest.fixture
def create_comments(news, author):
    """Фикстура создаёт комментарии с разными датами создания."""
    from news.models import Comment  # Импортируем здесь, если нужно
    now = timezone.now()
    for index in range(10):
        comment = Comment.objects.create(
            news=news,
            author=author,
            text=f'Текст {index}',
        )
        comment.created = now + timedelta(days=index)
        comment.save()
