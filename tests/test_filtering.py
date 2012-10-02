"""Unit tests for output filtering and changing filter."""

import unittest

import utils

class TestFiltering(utils.TestCase):
    def test_default_filter(self):
        self.assertEqual(self.render("{% template %}{{ 'a&z' }}"), 'a&amp;z')

    def test_set_filter(self):
        self.assertEqual(self.render(r"""
{% template val %}
{% filt = lambda s: repr(s) %}
{{ val }}
{% filt = symplate.html_filter %}
{{ val }}
""", val='"'), u"'\"'\n&#34;\n")

    def test_raw(self):
        self.assertEqual(self.render("{% template %}{{ !'<b>' }}"), '<b>')

    def test_override_default_filter_string(self):
        renderer = utils.Renderer(default_filter='lambda s: s.upper()')
        self.assertEqual(self.render("{% template %}{{ 'a&z' }}", _renderer=renderer), 'A&Z')

    def test_override_default_filter_function(self):
        filenames = []
        def my_filter(filename):
            filenames.append(filename)
            return 'lambda s: s.lower()'
        renderer = utils.Renderer(default_filter=my_filter)
        self.assertEqual(self.render("{% template %}{{ 'A&Z' }}", _renderer=renderer), 'a&z')
        self.assertEqual(self.render("{% template %}{{ 'Z&A' }}", _renderer=renderer), 'z&a')
        # at least test that filenames were different, and that they end with .symp
        self.assertEqual(len(set(filenames)), 2)
        self.assertTrue(filenames[0].endswith('.symp'))
        self.assertTrue(filenames[1].endswith('.symp'))

if __name__ == '__main__':
    unittest.main()
