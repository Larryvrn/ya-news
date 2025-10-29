"""Тесты для маршрутов (URL) приложения news.

Pytest-версия тестов из news/tests/test_routes.py.
"""
import pytest
from http import HTTPStatus

from pytest_lazy_fixtures import lf
from pytest_django.asserts import assertRedirects
from django.urls import reverse  # type: ignore


@pytest.mark.django_db
@pytest.mark.parametrize(
    # Имя параметра функции, передаём пустой кортеж или фикстуру.
    'name, args',
    # Значения, которые будут передаваться в name.
    (
        ('news:home', ()),
        ('news:detail', (lf('news.pk'),)),  # Фикстуру новости передаем тут
        ('users:login', ()),
        ('users:signup', ()),
    ),
)
def test_pages_avilability(client, name, args):
    """Тестирует доступность основных страниц приложения.

    Проверяет, что главная страница, страница новости,
    страницы логина и регистрации возвращают статус 200 OK.
    """
    url = reverse(name, args=args)  # Получаем ссылку на нужный адрес
    response = client.get(url)
    assert response.status_code == HTTPStatus.OK


@pytest.mark.django_db
@pytest.mark.parametrize(
    'param_client, expected_status',
    (
        (lf('author_client'), HTTPStatus.OK),
        (lf('not_author_client'), HTTPStatus.NOT_FOUND),
    ),
)
@pytest.mark.parametrize(
    'name',
    ('news:edit', 'news:delete'),
)
def test_avilability_for_comment_edit_and_delete(
    param_client,
    expected_status,
    name,
    comment
):
    """Тестирует доступность страниц редактирования и удаления комментариев.

    Проверяет, что автор комментария имеет доступ к страницам,
    а другие пользователи получают 404 ошибку.
    """
    # Формируем URL для страницы редактирования или удаления комментария
    # Используем фикстуру comment для получения ID существующего комментария
    url = reverse(name, args=(comment.id,))
    # Выполняем GET-запрос к странице с использованием переданного клиента
    # param_client автоматически подставляется из параметризации:
    # - author_client для автора комментария (ожидается 200 OK)
    # - not_author_client для другого пользователя (ожидается 404 Not Found)
    response = param_client.get(url)
    # Проверяем, что фактический статус ответа соответствует ожидаемому
    # Для автора: 200 OK (доступ разрешен)
    # Для не-автора: 404 Not Found (доступ запрещен)
    assert response.status_code == expected_status


@pytest.mark.django_db
@pytest.mark.parametrize(
    'name',
    ('news:edit', 'news:delete'),
)
def test_redirect_for_anonymous_client(client, name, comment):
    """Тестирует редирект анонимных пользователей.

    Проверяет, что анонимные пользователи при попытке редактирования
    или удаления комментария перенаправляются на страницу логина
    с параметром next.
    """
    # Получаем адрес страницы редактирования/удаления комментария:
    url = reverse(name, args=(comment.id,))
    # Получаем ожидаемый адрес страницы логина:
    login_url = reverse('users:login')
    # Формируем полный URL редиректа с параметром next:
    redirect_url = f'{login_url}?next={url}'
    response = client.get(url)
    # Проверяем редирект:
    assertRedirects(response, redirect_url)
