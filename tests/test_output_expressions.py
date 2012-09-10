"""Unit tests for output expressions."""

import unittest

import utils

class TestOutputExpressions(utils.TestCase):
    def test_basic(self):
        t = "{% template v='' %}"
        self.assertEqual(self.render(t + "a{{ '<' }}c"), 'a&lt;c')
        self.assertEqual(self.render(t + "a {{'<'}} c"), 'a &lt; c')
        self.assertEqual(self.render(t + "{{'a'}} {{'<'}} {{'c'}}"), 'a &lt; c')
        self.assertEqual(self.render(t + "a{{ v }}c", v='<'), 'a&lt;c')

    def test_before_template(self):
        self.assertTemplateError(1, 'one', self.render, 'one\ntwo')

    def test_outside_template(self):
        self.assertTemplateError(3, 'foo', self.render, '{% template %}\n{% end %}\nfoo')

    def test_multiline(self):
        self.assertEqual(self.render("{% template %}{{ '<' +\n'>' }}"), '&lt;&gt;')

    def test_contains_code_block(self):
        self.assertTemplateError(2, 'foo', self.render, "{% template %}\n{{ foo {% }}")
        # TODO: it's quirky that this shows line 1: {% template %} ...
        self.assertTemplateError(1, 'template', self.render, "{% template %}\n{{ foo %} }}")

if __name__ == '__main__':
    unittest.main()
