"""Модуль тестирования отображения контента приложения новостей.

Содержит тесты для проверки:
- Количества новостей на главной странице согласно настройкам
- Порядка сортировки новостей и комментариев
- Доступности форм комментариев для разных типов пользователей
- Корректности передачи данных в контекст шаблонов
"""
import pytest

from django.conf import settings  # type: ignore
from django.urls import reverse  # type: ignore

from news.forms import CommentForm


@pytest.mark.django_db
def test_news_count(client, create_news):
    """Проверяет количество новостей на главной странице.

    Убеждается, что количество не превышает установленный лимит.
    """
    # Загружаем главную страницу
    home_url = reverse('news:home')
    response = client.get(home_url)
    # Получаем список объектов из словаря контекста
    object_list = response.context['object_list']
    # Определяем количество записей в списке
    news_count = object_list.count()
    # Проверяем, что на странице именно NEWS_COUNT_ON_HOME_PAGE новостей
    assert news_count == settings.NEWS_COUNT_ON_HOME_PAGE


@pytest.mark.django_db
def test_news_order(client, create_news):
    """Тест: Новости на главной странице отсортированы от свежих к старым."""
    home_url = reverse('news:home')
    response = client.get(home_url)
    object_list = response.context['object_list']
    # Получаем даты новостей в том порядке, как они выведены на странице
    all_dates = [news.date for news in object_list]
    # Сортируем полученный список по убыванию
    sorted_dates = sorted(all_dates, reverse=True)
    # Проверяем, что исходный список был отсортирован правильно
    assert all_dates == sorted_dates


@pytest.mark.django_db
def test_comments_order(client, news, create_comments):
    """Тест:Комментарии на странице новости отсортированы от старых к новым."""
    detail_url = reverse('news:detail', args=(news.id,))
    response = client.get(detail_url)
    # Проверяем, что объект новости находится в словаре контекста
    assert 'news' in response.context
    # Получаем объект новости
    news_obj = response.context['news']
    # Получаем все комментарии к новости
    all_comments = news_obj.comment_set.all()
    # Собираем временные метки всех комментариев
    all_timestamps = [comment.created for comment in all_comments]
    # Сортируем временные метки по возрастанию (старые → новые)
    sorted_timestamps = sorted(all_timestamps)
    # Проверяем, что временные метки отсортированы правильно
    assert all_timestamps == sorted_timestamps


@pytest.mark.django_db
def test_anonymous_client_has_no_form(client, news):
    """Тест: Анонимному пользователю не доступна форма для комментария."""
    detail_url = reverse('news:detail', args=(news.id,))
    response = client.get(detail_url)
    # Проверяем, что формы нет в контексте
    assert 'form' not in response.context


@pytest.mark.django_db
def test_authorized_client_has_form(author_client, news):
    """Тест: Авторизованному пользователю доступна форма для комментария."""
    detail_url = reverse('news:detail', args=(news.id,))
    response = author_client.get(detail_url)
    # Проверяем, что форма есть в контексте
    assert 'form' in response.context
    # Проверяем, что объект формы соответствует нужному классу формы
    assert isinstance(response.context['form'], CommentForm)
