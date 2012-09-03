"""Unit tests for output filtering and changing _filter."""

import unittest

import utils

class TestFiltering(utils.TestCase):
    def test_default_filter(self):
        output = self.render("""{% template val %}
{{val}}""", val='<b>')
        self.assertEqual(output, u'&lt;b&gt;')

    def test_set_filter(self):
        pass

    def test_raw(self):
        pass

if __name__ == '__main__':
    unittest.main()