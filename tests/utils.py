"""Utility functions for unit tests."""

from __future__ import with_statement

import os
import sys
import unittest

import symplate

TEMPLATE_DIR = os.path.join(os.path.dirname(__file__), 'symplates')
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), 'symplouts')

class Renderer(symplate.Renderer):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault('template_dir', TEMPLATE_DIR)
        kwargs.setdefault('output_dir', OUTPUT_DIR)
        kwargs.setdefault('check_mtime', True)
        super(Renderer, self).__init__(*args, **kwargs)

renderer = Renderer()

class TestCase(unittest.TestCase):
    def setUp(self):
        # would use setUpClass, but that's Python 2.7+ only
        cls = self.__class__
        if not hasattr(cls, '_class_set_up'):
            cls._class_set_up = True
            TestCase._template_num = 0

    def _write_template(self, _renderer, name, template):
        if isinstance(template, unicode):
            template = template.encode('utf-8')
        filename = os.path.join(_renderer.template_dir, name + _renderer.extension)
        dirname = os.path.dirname(filename)
        if not os.path.exists(dirname):
            os.makedirs(dirname)
        with open(filename, 'w') as f:
            f.write(template)
        return filename

    def render(self, template, *args, **kwargs):
        """Compile and render template source string with given args."""
        _strip = kwargs.pop('_strip', True)
        _renderer = kwargs.pop('_renderer', renderer)
        _increment = kwargs.pop('_increment', 1)

        TestCase._template_num += _increment
        try:
            frame = sys._getframe(1)
            while not frame.f_code.co_name.startswith('test_'):
                frame = frame.f_back
            name = '_' + frame.f_code.co_name[5:]
        except Exception:
            # Python implementation doesn't support _getframe, use numbered
            # template names
            name = ''
        name = '%s/test%s_%d' % (self.__class__.__name__,
                                name, TestCase._template_num)
        self._write_template(_renderer, name, template)

        output = _renderer.render(name, *args, **kwargs)
        if _strip:
            output = output.strip()
        return output

    def assertTemplateError(self, line_num, text_contains, func, *args, **kwargs):
        """Ensure func(*args, **kwargs) raises symplate.Error, with given 
        line number and text if not None.
        """
        try:
            func(*args, **kwargs)
        except symplate.Error, error:
            if line_num is not None:
                self.assertEqual(line_num, error.line_num)
            if text_contains is not None:
                self.assertTrue(text_contains in error.text,
                        'text %r not in %r' % (text_contains, error.text))
        else:
            self.assertTrue(False, 'symplate.Error not raised')
