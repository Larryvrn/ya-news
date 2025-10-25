# news/tests/test_trial.py
from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from unittest import skip
# Получаем модель пользователя.
User = get_user_model()


@skip()
class TestNews(TestCase):

    @classmethod
    def setUpTestData(cls):
        # Создаём пользователя.
        cls.user = User.objects.create(username='testUser')
        # Создаём объект клиента.
        cls.user_client = Client()
        # "Логинимся" в клиенте при помощи метода force_login().        
        cls.user_client.force_login(cls.user)
        # Теперь через этот клиент можно отправлять запросы
        # от имени пользователя с логином "testUser". 

    # def test_successful_creation(self):
    #     news_count = News.objects.count()
    #     self.assertEqual(news_count, 1)

    # def test_title(self):
    #     # Чтобы проверить равенство с константой -
    #     # обращаемся к ней через self, а не через cls:
    #     self.assertEqual(self.news.title, self.TITLE)