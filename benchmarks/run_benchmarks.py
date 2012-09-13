"""Run all benchmarks."""

# TODO: ensure compile() compiles included templates too, or at least that it's the same for everyone (render too)

from __future__ import with_statement

import collections
import os
import sys
import timeit
import warnings

BlogEntry = collections.namedtuple('BlogEntry', 'title url html_body')

TITLE = 'My Blog'
ENTRIES = [
    BlogEntry(u'<Sorry>', u'/sorry/?a=b&c=d', u'<p>Sorry for the lack of updates.</p>'),
    BlogEntry(u'My life & story', None, u'<p>Once upon a time...</p>'),
    BlogEntry(u'First \u201cpost\u201d', u'/first-post/', u'<p>This is the first post.</p>'),
]
ENTRIES *= 10  # To give the render test a bit more to chew on

def rel_dir(dirname):
    """Return full directory name of dirname from this file's directory."""
    return os.path.abspath(os.path.join(os.path.dirname(__file__), dirname))

class TemplateLanguage(object):
    num_compiles = 10
    num_renders = 100

    def setup_compile(self):
        pass

    def compile(self):
        raise NotImplementedError

    def setup_render(self):
        pass

    def render(self):
        raise NotImplementedError

    def benchmark(self):
        timings = {}
        self.setup_compile()
        timings['compile'] = min(timeit.repeat(self.compile, number=self.num_compiles)) / float(self.num_compiles)
        self.setup_render()
        timings['render'] = min(timeit.repeat(self.render, number=self.num_renders)) / float(self.num_renders)
        return timings

try:
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
    import symplate
except ImportError:
    warnings.warn("Can't import symplate, is it in your PYTHONPATH?")
    symplate = None
if symplate:
    class Symplate(TemplateLanguage):
        def __init__(self):
            self.renderer = symplate.Renderer(
                    template_dir=rel_dir('symplate'),
                    output_dir=rel_dir('symplate_output'),
                    modify_path=False)

        def compile(self):
            return self.renderer.compile('main')

        def render(self):
            return self.renderer.render('main', title=TITLE, entries=ENTRIES)

try:
    import Cheetah.Template as cheetah
    from Cheetah.Filters import WebSafe as cheetah_websafe
except ImportError:
    warnings.warn("Can't import Cheetah, is it in your PYTHONPATH?")
    cheetah = None
if cheetah:
    cheetah.checkFileMtime(False)

    class Cheetah(TemplateLanguage):
        def __init__(self):
            self.template_dir = rel_dir('cheetah')

        def compile(self):
            file_name = os.path.join(self.template_dir, 'main.tmpl')
            return cheetah.Template.compile(
                    file=file_name, cacheCompilationResults=False, useCache=False)

        def setup_render(self):
            self.template = self.compile()

        def render(self):
            params = dict(title=TITLE, entries=ENTRIES, template_dir=self.template_dir)
            return self.template(searchList=[params], filter=cheetah_websafe).respond()

try:
    import jinja2
except ImportError:
    warnings.warn("Can't import jinja2, is it in your PYTHONPATH?")
    jinja2 = None
if jinja2:
    class Jinja2(TemplateLanguage):
        def __init__(self):
            loader = jinja2.FileSystemLoader(rel_dir('jinja2'))
            self.compile_env = jinja2.Environment(loader=loader, autoescape=True, cache_size=0)
            self.render_env = jinja2.Environment(loader=loader, autoescape=True)

        def compile(self):
            return self.compile_env.get_template('main.tmpl')

        def setup_render(self):
            self.template = self.render_env.get_template('main.tmpl')

        def render(self):
            return self.template.render(title=TITLE, entries=ENTRIES)

def main():
    language_classes = sorted((name, cls) for name, cls in globals().items()
                              if isinstance(cls, type) and
                                 issubclass(cls, TemplateLanguage) and
                                 cls is not TemplateLanguage)
    for name, cls in language_classes:
        language = cls()
        timings = language.benchmark()
        print '%.20s %.3f %.3f' % (name, timings['compile'] * 1000, timings['render'] * 1000)
        with open(os.path.join(rel_dir(''), name.lower() + '.html'), 'w') as f:
            language.setup_render()
            f.write(language.render().encode('utf-8'))

if __name__ == '__main__':
    main()