"""Модуль тестирования бизнес-логики приложения новостей.

Содержит тесты для проверки:
- Создания комментариев авторизованными и анонимными пользователями
- Валидации текста комментариев на наличие запрещенных слов
- Редактирования и удаления комментариев с проверкой прав доступа
- Изоляции данных между разными пользователями
"""
import pytest
from http import HTTPStatus

from django.urls import reverse  # type: ignore
from pytest_django.asserts import assertRedirects  # type: ignore

from news.forms import BAD_WORDS, WARNING
from news.models import Comment


# Тексты для комментариев - выносим в константы для переиспользования
COMMENT_TEXT = 'Текст комментария'
NEW_COMMENT_TEXT = 'Обновлённый комментарий'


@pytest.mark.django_db
def test_anonymous_user_cant_create_comment(client, news):
    """Тест: Анонимный пользователь не может создать комментарий."""
    # Формируем URL страницы новости
    url = reverse('news:detail', args=(news.id,))
    # Данные для формы комментария
    form_data = {'text': COMMENT_TEXT}
    # Отправляем POST-запрос от анонимного пользователя
    client.post(url, data=form_data)
    # Проверяем, что комментарий не создался
    comments_count = Comment.objects.count()
    assert comments_count == 0


@pytest.mark.django_db
def test_user_can_create_comment(author_client, news, author):
    """Тест: Авторизованный пользователь может создать комментарий."""
    # Формируем URL страницы новости
    url = reverse('news:detail', args=(news.id,))
    # Данные для формы комментария
    form_data = {'text': COMMENT_TEXT}
    # Отправляем POST-запрос от авторизованного пользователя
    response = author_client.post(url, data=form_data)
    # Проверяем редирект на страницу с комментариями
    assertRedirects(response, f'{url}#comments')
    # Проверяем, что комментарий создался
    comments_count = Comment.objects.count()
    assert comments_count == 1
    # Проверяем атрибуты созданного комментария
    comment = Comment.objects.get()
    assert comment.text == COMMENT_TEXT
    assert comment.news == news
    assert comment.author == author


@pytest.mark.django_db
def test_user_cant_use_bad_words(author_client, news):
    """Тест: Пользователь не может использовать запрещённые слова."""
    # Формируем текст с запрещённым словом
    bad_words_data = {'text': f'Какой-то текст, {BAD_WORDS[0]}, еще текст'}
    url = reverse('news:detail', args=(news.id,))
    # Отправляем POST-запрос с запрещённым словом
    response = author_client.post(url, data=bad_words_data)
    # Проверяем, что в форме есть ошибка
    assert 'form' in response.context
    form = response.context['form']
    assert 'text' in form.errors
    assert WARNING in form.errors['text']
    # Проверяем, что комментарий не создался
    comments_count = Comment.objects.count()
    assert comments_count == 0


@pytest.mark.django_db
def test_author_can_delete_comment(author_client, comment, news):
    """Тест: Автор может удалить свой комментарий."""
    # Формируем URL для удаления комментария
    delete_url = reverse('news:delete', args=(comment.id,))
    # Формируем ожидаемый URL редиректа (к комментариям новости)
    news_url = reverse('news:detail', args=(news.id,))
    url_to_comments = f'{news_url}#comments'
    # Отправляем DELETE-запрос от автора комментария
    response = author_client.delete(delete_url)
    # Проверяем редирект на страницу с комментариями
    assertRedirects(response, url_to_comments)
    # Проверяем статус код (302 Found - редирект)
    assert response.status_code == HTTPStatus.FOUND
    # Проверяем, что комментарий удалился
    comments_count = Comment.objects.count()
    assert comments_count == 0


@pytest.mark.django_db
def test_user_cant_delete_comment_of_another_user(not_author_client, comment):
    """Тест: Пользователь не может удалить чужой комментарий."""
    delete_url = reverse('news:delete', args=(comment.id,))
    # Отправляем DELETE-запрос от пользователя, который не автор
    response = not_author_client.delete(delete_url)
    # Проверяем, что вернулась 404 ошибка (доступ запрещён)
    assert response.status_code == HTTPStatus.NOT_FOUND
    # Проверяем, что комментарий остался в базе
    comments_count = Comment.objects.count()
    assert comments_count == 1


@pytest.mark.django_db
def test_author_can_edit_comment(author_client, comment, news):
    """Тест: Автор может редактировать свой комментарий."""
    # Формируем URL для редактирования комментария
    edit_url = reverse('news:edit', args=(comment.id,))
    # Формируем ожидаемый URL редиректа
    news_url = reverse('news:detail', args=(news.id,))
    url_to_comments = f'{news_url}#comments'
    # Данные для обновления комментария
    form_data = {'text': NEW_COMMENT_TEXT}
    # Отправляем POST-запрос на редактирование от автора
    response = author_client.post(edit_url, data=form_data)
    # Проверяем редирект на страницу с комментариями
    assertRedirects(response, url_to_comments)
    # Обновляем объект комментария из базы
    comment.refresh_from_db()
    # Проверяем, что текст комментария обновился
    assert comment.text == NEW_COMMENT_TEXT


@pytest.mark.django_db
def test_user_cant_edit_comment_of_another_user(not_author_client, comment):
    """Тест: Пользователь не может редактировать чужой комментарий."""
    edit_url = reverse('news:edit', args=(comment.id,))
    form_data = {'text': NEW_COMMENT_TEXT}
    # Отправляем POST-запрос на редактирование от не-автора
    response = not_author_client.post(edit_url, data=form_data)
    # Проверяем, что вернулась 404 ошибка
    assert response.status_code == HTTPStatus.NOT_FOUND
    # Обновляем объект комментария из базы
    comment.refresh_from_db()
    # Проверяем, что текст комментария НЕ изменился
    assert comment.text == COMMENT_TEXT
