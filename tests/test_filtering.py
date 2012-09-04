"""Unit tests for output filtering and changing _filter."""

import unittest

import utils

class TestFiltering(utils.TestCase):
    def test_default_filter(self):
        self.assertEqual(self.render(r"""
{% template %}
{{ '<b>' }}
"""), u'&lt;b&gt;')

    def test_set_filter(self):
        self.assertEqual(self.render(r"""
{% import json %}
{% template %}
{% _filter = lambda s: repr(s) %}
{{ 'foo\nbar' }}
"""), u"'foo\\nbar'")

    def test_raw(self):
        pass

if __name__ == '__main__':
    unittest.main()