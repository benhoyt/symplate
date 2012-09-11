"""Run all benchmarks."""

from __future__ import with_statement

import collections
import os
import sys
import timeit
import warnings

BlogEntry = collections.namedtuple('BlogEntry', 'title url html_body')

blog_entries = [
    BlogEntry(u'<Sorry>', u'/sorry/?a=b&c=d', u'<p>Sorry for the lack of updates.</p>'),
    BlogEntry(u'My life & story', None, u'<p>Once upon a time...</p>'),
    BlogEntry(u'First \u201cpost\u201d', u'/first-post/', u'<p>This is the first post.</p>'),
]
blog_entries *= 10  # To give the render test a bit more to chew on

def rel_dir(dirname):
    """Return full directory name of dirname from this file's directory."""
    return os.path.abspath(os.path.join(os.path.dirname(__file__), dirname))

class TemplateLanguage(object):
    num_compiles = 1000
    num_renders = 1000

    def compile_main(self):
        return self.compile('main')

    def render_main(self):
        return self.render('main', title='My Blog', entries=blog_entries)

    def benchmark(self):
        timings = {}
        timings['compile'] = min(timeit.repeat(self.compile_main, number=self.num_compiles)) / float(self.num_compiles)
        timings['render'] = min(timeit.repeat(self.render_main, number=self.num_renders)) / float(self.num_renders)
        return timings

try:
    import symplate
except ImportError:
    warnings.warn("Can't import symplate, is symplate.py in your PYTHONPATH?")
    symplate = None
if symplate:
    class Symplate(TemplateLanguage):
        def __init__(self):
            self.renderer = symplate.Renderer(
                    template_dir=rel_dir('symplate'),
                    output_dir=rel_dir('symplate_output'),
                    modify_path=False)

        def compile(self, name):
            return self.renderer.compile(name)

        def render(self, name, **kwargs):
            return self.renderer.render(name, **kwargs)

try:
    import Cheetah.Template as cheetah
    from Cheetah.Filters import WebSafe as cheetah_websafe
except ImportError:
    warnings.warn("Can't import Cheetah, is Cheetah in your PYTHONPATH?")
    cheetah = None
if cheetah:
    cheetah.checkFileMtime(False)

    class Cheetah(TemplateLanguage):
        num_compiles = 100

        def __init__(self):
            self.template_dir = rel_dir('cheetah')

        def compile(self, name):
            file_name = os.path.join(self.template_dir, name + '.tmpl')
            self.template = cheetah.Template.compile(
                    file=file_name, cacheCompilationResults=False, useCache=False)
            self.template_name = name
            return self.template

        def render(self, name, **kwargs):
            assert name == self.template_name
            params = dict(kwargs, template_dir=self.template_dir)
            return self.template(searchList=[params], filter=cheetah_websafe).respond()

def main():
    language_classes = sorted((name, cls) for name, cls in globals().items()
                              if isinstance(cls, type) and
                                 issubclass(cls, TemplateLanguage) and
                                 cls is not TemplateLanguage)
    for name, cls in language_classes:
        language = cls()
        timings = language.benchmark()
        print '%.20s %.3f %.3f' % (name, timings['compile'] * 1000, timings['render'] * 1000)
        with open(name.lower() + '.html', 'w') as f:
            language.compile_main()
            f.write(language.render_main().encode('utf-8'))

if __name__ == '__main__':
    main()