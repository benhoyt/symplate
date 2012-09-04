"""Utility functions for unit tests."""

import os
import sys
import unittest

import symplate

TEMPLATE_DIR = os.path.join(os.path.dirname(__file__), 'symplates')
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), 'symplouts')

class Renderer(symplate.Renderer):
    def __init__(self, *args, **kwargs):
        super(Renderer, self).__init__(*args, **kwargs)
        self.template_dir = TEMPLATE_DIR
        self.output_dir = OUTPUT_DIR
        self.check_mtime = True

renderer = Renderer()

class TestCase(unittest.TestCase):
    _template_num = 0

    def _write_template(self, name, template):
        if isinstance(template, unicode):
            template = template.encode('utf-8')
        filename = os.path.join(TEMPLATE_DIR, name + '.symp')
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
        TestCase._template_num += 1
        try:
            name = '_' + sys._getframe(1).f_code.co_name
        except Exception:
            # Python implementation doesn't support _getframe, use numbered
            # template names
            name = ''
        name = '%s/test_%d%s' % (self.__class__.__name__,
                                 TestCase._template_num, name)
        self._write_template(name, template)
        output = _renderer.render(name, *args, **kwargs)
        if _strip:
            output = output.strip()
        return output
