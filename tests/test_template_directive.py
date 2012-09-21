"""Unit tests for the {% template ... %} directive."""

import unittest

import utils

class TestTemplateDirective(utils.TestCase):
    def test_no_args(self):
        template = "{% template %}a{{'b'}}c"
        self.assertEqual(self.render(template), 'abc')
        self.assertRaises(TypeError, self.render, template, foo='bar')

    def test_positional_args(self):
        template = '{% template one, two %}{{one}}.{{two}}'
        self.assertEqual(self.render(template, 'ONE', 'TWO'), 'ONE.TWO')
        self.assertEqual(self.render(template, one='One', two='Two'), 'One.Two')
        self.assertEqual(self.render(template, two='B', one='A'), 'A.B')
        self.assertRaises(TypeError, self.render, template, 1)
        self.assertRaises(TypeError, self.render, template, 1, 2, 3)
        self.assertRaises(TypeError, self.render, template, 1, 2, three='Three')

    def test_keyword_args(self):
        template = "{% template one='a', two='b' %}{{one}}.{{two}}"
        self.assertEqual(self.render(template), 'a.b')
        self.assertEqual(self.render(template, 'A'), 'A.b')
        self.assertEqual(self.render(template, two='B'), 'a.B')
        self.assertEqual(self.render(template, 'ONE', 'TWO'), 'ONE.TWO')
        self.assertEqual(self.render(template, one='One', two='Two'), 'One.Two')
        self.assertEqual(self.render(template, two='B', one='A'), 'A.B')
        self.assertRaises(TypeError, self.render, template, 1, 2, 3)
        self.assertRaises(TypeError, self.render, template, 1, 2, three='Three')

    def test_directive_whitespace(self):
        self.assertEqual(self.render('{% template %}T'), 'T')
        self.assertEqual(self.render('{%template%}T'), 'T')
        self.assertEqual(self.render('{%\ttemplate\t%}T'), 'T')
        self.assertEqual(self.render('{% template v %}{{v}}', v='V'), 'V')
        self.assertEqual(self.render('{% template\tv %}{{v}}', v='V'), 'V')

    def test_strip_eol_after(self):
        self.assertEqual(self.render("\n\n {% template %} \n {{ 'a' }}"), ' \n a')
        self.assertEqual(self.render("\n\n {% template %}\n\n {{ 'a' }}"), '\n a')

    def test_strip_whitespace_on_line_before(self):
        self.assertEqual(self.render("{% template %}\n  \t\t  {% x = 42 %}"), '')
        self.assertEqual(self.render("{% template %}\n  \n\n  {% x = 42 %}"), '  \n\n')

    def test_empty(self):
        self.assertEqual(self.render('{% template %}'), '')
        self.assertTemplateError(1, None, self.render, '')
        self.assertTemplateError(2, None, self.render, '\n\n')

    def test_no_directive(self):
        self.assertTemplateError(2, '#two', self.render, '{% #one %}\n{% #two %}')

    def test_at_top_level(self):
        self.assertTemplateError(2, 'template', self.render, '{% while 1: %}\n{% template %}')

    def test_end_top_level(self):
        self.assertTemplateError(2, 'while', self.render, '{% template %}\n{% while 1: %}')
        self.assertTemplateError(3, 'while', self.render, '{% template %}\n{% end %}\n{% while 1: %}')

    def test_multiple(self):
        self.assertTemplateError(2, 'bar', self.render, '{% template %}foo{% end %}\n{% template %}bar')

if __name__ == '__main__':
    unittest.main()
