"""Unit tests for html_filter."""

import unittest

from symplate import html_filter

class TestHtmlFilter(unittest.TestCase):
    def test_none(self):
        self.assertEqual(html_filter(None), '')

    def test_str(self):
        self.assertEqual(html_filter('foo'), 'foo')
        self.assertEqual(html_filter('\xe2\x80\x99'), u'\u2019')
        self.assertRaises(UnicodeError, html_filter, '\xff')

    def test_unicode(self):
        self.assertEqual(html_filter(u'\u2019'), u'\u2019')
        self.assertEqual(html_filter(u'<\u2019>'), u'&lt;\u2019&gt;')

    def test_non_string(self):
        self.assertEqual(html_filter(1234), '1234')

    def test_special_chars(self):
        self.assertEqual(html_filter('foo &<>\'" bar'), 'foo &amp;&lt;&gt;&#39;&quot; bar')

    def test_non_unicodeable(self):
        class NonUnicodeable(object):
            def __str__(self):
                return '\xff'
        self.assertRaises(UnicodeError, html_filter, NonUnicodeable())

if __name__ == '__main__':
    unittest.main()