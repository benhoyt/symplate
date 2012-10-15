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
        self.assertTemplateError(1, 'template', self.render, "{% template %}\n{{ foo %} }}")

    def test_python_name_error(self):
        self.assertRaises(NameError, self.render, '{% template %}{{ asdf }}')

    def test_python_syntax_error(self):
        self.assertRaises(SyntaxError, self.render, '{% template %}{{ $$$ }}')

    def test_no_comment(self):
        self.assertRaises(SyntaxError, self.render, '{% template %}{{ # no comment }}')

    def test_no_close(self):
        self.assertTemplateError(2, 'foo', self.render, '{% template %}\n{{ foo')

    def test_multiple_closes(self):
        self.assertTemplateError(2, 'bar', self.render, '{% template %}\n{{ bar }} }}')

    def test_empty(self):
        self.assertEqual(self.render('{% template %}{{ }}'), '')

    def test_empty_raw(self):
        self.assertEqual(self.render('{% template %}{{ ! }}'), '')

    def test_outside_template(self):
        self.assertTemplateError(1, 'foo', self.render, 'foo')

if __name__ == '__main__':
    unittest.main()
