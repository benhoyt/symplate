"""Unit tests for straight text output."""

import unittest

import utils

class TestText(utils.TestCase):
    def test_short_string(self):
        self.assertEqual(self.render('{% template %}short'), 'short')
        self.assertEqual(self.render('{% template %}short\n2'), 'short\n2')
        self.assertEqual(self.render('{% template %}longer but not multiline and quick brown foxes jump over lazy dogs'),
                         'longer but not multiline and quick brown foxes jump over lazy dogs')

    def test_long_string(self):
        content = r"""This is a longer string
which definitely should
be broken, and it should
should work fine, as should\nescapes."""
        self.assertEqual(self.render('{% template %}' + content), content)
        content = content.replace(' it ', ' """ ')
        self.assertEqual(self.render('{% template %}' + content), content)
        content = '"""' + content + '"""'
        self.assertEqual(self.render('{% template %}' + content), content)

    def test_before_after_output(self):
        self.assertEqual(self.render('{% template %}a{{"b"}}c'), 'abc')

if __name__ == '__main__':
    unittest.main()
