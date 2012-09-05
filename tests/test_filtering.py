"""Unit tests for output filtering and changing _filter."""

import unittest

import utils

class TestFiltering(utils.TestCase):
    def test_default_filter(self):
        self.assertEqual(self.render("{% template %}{{ 'a&z' }}"), 'a&amp;z')

    def test_set_filter(self):
        self.assertEqual(self.render(r"""
{% template val %}
{% _filter = lambda s: repr(s) %}
{{ val }}
{% _filter = symplate.html_filter %}
{{ val }}
""", val='"'), u"'\"'\n&quot;")

    def test_raw(self):
        self.assertEqual(self.render("{% template %}{{ !'<b>' }}"), '<b>')

    def test_override_default_filter(self):
        filenames = set()
        class OverrideRenderer(utils.Renderer):
            def get_default_filter(self, filename):
                filenames.add(filename)
                return 'lambda s: s.upper()'
        renderer = OverrideRenderer()
        self.assertEqual(self.render("{% template %}{{ 'a&z' }}", _renderer=renderer), 'A&Z')
        self.assertEqual(self.render("{% template %}{{ 'z&a' }}", _renderer=renderer), 'Z&A')
        # at least test that filenames were different
        self.assertEqual(len(filenames), 2)

if __name__ == '__main__':
    unittest.main()
