from django.test import SimpleTestCase


class FrontendTest(SimpleTestCase):
    def test_home_page_renders_the_single_page_app(self):
        response = self.client.get('/')

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'index.html')
        self.assertContains(response, 'Twitter Clone')
