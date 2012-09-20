"""Unit tests for html_filter."""

import unittest

from symplate import html_filter

class TestHtmlFilter(unittest.TestCase):
    def test_str(self):
        self.assertEqual(html_filter('foo'), 'foo')
        self.assertEqual(html_filter('foo &<>\'" bar'), 'foo &amp;&lt;&gt;&#39;&#34; bar')
        self.assertEqual(html_filter('\xe2\x80\x99'), '\xe2\x80\x99')
        self.assertEqual(html_filter('\xff'), '\xff')

    def test_unicode(self):
        self.assertEqual(html_filter(u'\u2019'), u'\u2019')
        self.assertEqual(html_filter(u'<\u2019>'), u'&lt;\u2019&gt;')
        self.assertEqual(html_filter(u'foo &<>\'" bar'), u'foo &amp;&lt;&gt;&#39;&#34; bar')

    def test_non_string(self):
        self.assertRaises(AttributeError, html_filter, 1234)

if __name__ == '__main__':
    unittest.main()