"""Unit tests for Renderer class and its keyword arg options."""

import os
import sys
import unittest

import utils

class TestRenderer(utils.TestCase):
    def test_template_dir(self):
        template_dir = os.path.join(os.path.dirname(__file__), 'symplates2')
        renderer = utils.Renderer(template_dir=template_dir)
        self.assertEquals(self.render('{% template %}ttd', _renderer=renderer), 'ttd')

    def test_output_dir(self):
        output_dir = os.path.join(os.path.dirname(__file__), 'symplouts2')
        renderer = utils.Renderer(output_dir=output_dir)
        self.assertEqual(self.render('{% template %}tod', _renderer=renderer), 'tod')
        py_files = [f for f in os.listdir(os.path.join(output_dir, 'TestRenderer'))
                    if f.endswith('.py')]
        self.assertEqual(len(py_files), 2)  # compiled template and __init__.py

    def test_extension(self):
        renderer = utils.Renderer(extension='.symp2')
        self.assertEquals(self.render('{% template %}te', _renderer=renderer), 'te')

    def test_check_mtimes_true(self):
        renderer = utils.Renderer(check_mtimes=True)
        self.assertEquals(self.render('{% template %}cmt1', _renderer=renderer), 'cmt1')
        self.assertEquals(self.render('{% template %}cmt2', _renderer=renderer, _increment=0, _adjust_mtime=5), 'cmt2')

    def test_check_mtimes_false(self):
        renderer = utils.Renderer(check_mtimes=True)
        self.assertEquals(self.render('{% template %}cmf1', _renderer=renderer), 'cmf1')
        renderer = utils.Renderer(check_mtimes=False)
        self.assertEquals(self.render('{% template %}cmf2', _renderer=renderer, _increment=0, _adjust_mtime=5), 'cmf2')
        self.assertEquals(self.render('{% template %}cmf3', _renderer=renderer, _increment=0, _adjust_mtime=5), 'cmf2')

    def test_modify_path(self):
        saved_path = list(sys.path)
        try:
            renderer = utils.Renderer(modify_path=False)
            for name, module in sys.modules.items():
                if 'symplouts' in name:
                    sys.modules.pop(name)
            path_dir = os.path.abspath(os.path.join(renderer.output_dir, '..'))
            while path_dir in sys.path:
                sys.path.remove(path_dir)
            self.assertRaises(ImportError, self.render, '{% template %}mp', _renderer=renderer)
            renderer = utils.Renderer(modify_path=True)
            self.assertEqual(self.render('{% template %}pm', _renderer=renderer), 'pm')
        finally:
            sys.path = saved_path

    def test_preamble(self):
        renderer = utils.Renderer(preamble="def preamble_func(): return '42'\n")
        self.assertEquals(self.render('{% template %}{{ preamble_func() }}', _renderer=renderer), '42')

if __name__ == '__main__':
    unittest.main()
