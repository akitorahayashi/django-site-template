from django.test import SimpleTestCase
from django.urls import reverse


class HelloIndexViewTests(SimpleTestCase):
    def test_root_returns_200(self):
        url = reverse("hello:index")
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)

    def test_page_has_expected_heading_and_title(self):
        url = reverse("hello:index")
        resp = self.client.get(url)
        self.assertContains(
            resp, "<h1>Welcome to your new Django project!</h1>", html=True
        )
        self.assertContains(resp, "<title>Django Project</title>", html=True)
        self.assertTemplateUsed(resp, "hello/index.html")
