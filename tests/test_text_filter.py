"""Unit tests for text_filter."""

import unittest

from symplate import text_filter

class TestTextFilter(unittest.TestCase):
    def test_str(self):
        self.assertEqual(text_filter('foo'), u'foo')
        self.assertEqual(text_filter('foo &<>\'" bar'), u'foo &<>\'" bar')
        self.assertEqual(text_filter('\xe2\x80\x99'), u'\u2019')
        self.assertRaises(UnicodeError, text_filter, '\xff')

    def test_unicode(self):
        self.assertEqual(text_filter(u'\u2019'), u'\u2019')
        self.assertEqual(text_filter(u'<\u2019>'), u'<\u2019>')
        self.assertEqual(text_filter(u'foo &<>\'" bar'), u'foo &<>\'" bar')

    def test_non_string(self):
        self.assertEqual(text_filter(1234), u'1234')
        self.assertEqual(text_filter(['<']), u"['<']")

    def test_none(self):
        self.assertEqual(text_filter(None), u'')

if __name__ == '__main__':
    unittest.main()