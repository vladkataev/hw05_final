from django.test import TestCase, Client
from django.urls import reverse
from http import HTTPStatus


class AboutTest(TestCase):
    def setUp(self):
        self.guest_client = Client()

    def test_about_urls(self):
        """Проверка доступности адресов статичных страниц"""
        about_urls = (reverse('about:author'), reverse('about:tech'))
        for url in about_urls:
            with self.subTest(url=url):
                response = self.guest_client.get(url)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_about_uses_correct_template(self):
        """Проверка шаблона для статичных страниц"""
        templates_pages_names = {
            reverse('about:author'): 'about/author.html',
            reverse('about:tech'): 'about/tech.html',
        }
        for url, template in templates_pages_names.items():
            with self.subTest(url=url):
                response = self.guest_client.get(url)
                self.assertTemplateUsed(response, template)
