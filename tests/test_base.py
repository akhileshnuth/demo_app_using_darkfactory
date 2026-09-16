import unittest

class BaseTemplateTest(unittest.TestCase):
    def test_footer_in_base_template(self):
        with open('templates/base.html') as f:
            content = f.read()
            self.assertIn('© 2026 Personal Document Vault', content)

if __name__ == '__main__':
    unittest.main()