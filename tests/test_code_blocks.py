"""Unit tests for code blocks."""

import unittest

import utils

class TestCodeBlocks(utils.TestCase):
    def test_comments(self):
        self.assertEqual(self.render('{% template %}a{% # comment %}b'), 'ab')

    def test_before_template(self):
        self.assertEqual(self.render("{% def f(): return 'xyz' %}{% template %}{{ f() }}"), 'xyz')

    def test_after_template(self):
        self.assertEqual(self.render("{% template %}{{ g() }}{% end %}{% def g(): return 'wxy' %}"), 'wxy')

    def test_multiline(self):
        self.assertEqual(self.render(r"""
{% template %}
{%
    # these are some
    # comments
    def func():
    return 'bar'
    end
%}
{{ func() }}
"""), 'bar')

    def test_end(self):
        t = "{% template %}{% for c in 'abc': %}{{ c }}"
        self.assertEqual(self.render(t + '{% end %}'), 'abc')
        self.assertEqual(self.render(t + '{%end%}'), 'abc')
        self.assertEqual(self.render(t + '{%\tend\t%}'), 'abc')
        self.assertEqual(self.render(t + '{% end xyz %}'), 'abc')
        self.assertEqual(self.render(t + '{% end\txyz %}'), 'abc')

    def test_extra_end(self):
        self.assertTemplateError(2, 'bar', self.render, '{% template %}a{% end foo %}\n{% end bar %}')

    def test_contains_output_expression(self):
        self.assertTemplateError(2, 'for', self.render, "{% template %}\n{% for x in y: {{ %}{% end %}")
        self.assertTemplateError(2, 'for', self.render, "{% template %}\n{% for x in y: }} %}{% end %}")

    def test_python_name_error(self):
        self.assertRaises(NameError, self.render, '{% template %}{% asdf %}')

    def test_python_syntax_error(self):
        self.assertRaises(SyntaxError, self.render, '{% template %}{% $$$ %}')

    def test_no_close(self):
        self.assertTemplateError(2, 'for', self.render, '{% template %}\n{% for x in y:')

    def test_multiple_closes(self):
        self.assertTemplateError(2, 'for', self.render, '{% template %}\n{% for x in y: %} %}')

    def test_empty(self):
        self.assertEqual(self.render('{% template %}a{% %}b'), 'ab')

    def test_surrounding_whitespace(self):
        self.assertEqual(self.render('{% template %}a{% #comment %}b'), 'ab')
        self.assertEqual(self.render('{% template %}a{% #comment %}\nb'), 'ab')
        self.assertEqual(self.render('{% template %}a{% #comment %}\n\nb'), 'a\nb')

if __name__ == '__main__':
    unittest.main()
