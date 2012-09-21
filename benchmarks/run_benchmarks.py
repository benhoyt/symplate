"""Run all benchmarks."""

from __future__ import with_statement

import collections
import os
import sys
import timeit
import warnings


BlogEntry = collections.namedtuple('BlogEntry', 'title url html_body')

TITLE = u'My Blog'
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
                    rel_dir('symplate'),
                    output_dir=rel_dir('symplate_output'),
                    modify_path=False)

        def compile(self):
            for name in ('header', 'main', 'footer'):
                self.renderer.compile(name)

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
            for name in ('header', 'main', 'footer'):
                file_name = os.path.join(self.template_dir, name + '.tmpl')
                cheetah.Template.compile(file=file_name, cacheCompilationResults=False, useCache=False)

        def setup_render(self):
            file_name = os.path.join(self.template_dir, 'main.tmpl')
            self.template = cheetah.Template.compile(file=file_name, cacheCompilationResults=True, useCache=True)

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
            self.compile_env = jinja2.Environment(loader=loader, autoescape=True, cache_size=0, trim_blocks=True)
            self.render_env = jinja2.Environment(loader=loader, autoescape=True, trim_blocks=True)

        def compile(self):
            for name in ('header', 'main', 'footer'):
                self.compile_env.get_template(name + '.tmpl')

        def setup_render(self):
            for name in ('header', 'main', 'footer'):
                self.render_env.get_template(name + '.tmpl')
            self.template = self.render_env.get_template('main.tmpl')

        def render(self):
            return self.template.render(title=TITLE, entries=ENTRIES)


try:
    import mako.lookup
except ImportError:
    warnings.warn("Can't import mako, is it in your PYTHONPATH?")
    mako = None
if mako:
    class Mako(TemplateLanguage):
        def __init__(self):
            self.compile_lookup = mako.lookup.TemplateLookup(
                    directories=[rel_dir('mako')],
                    default_filters=['h'],
                    collection_size=0)
            self.render_lookup = mako.lookup.TemplateLookup(
                    directories=[rel_dir('mako')],
                    default_filters=['h'])

        def compile(self):
            for name in ('header', 'main', 'footer'):
                self.compile_lookup.get_template(name + '.tmpl')

        def setup_render(self):
            for name in ('header', 'main', 'footer'):
                self.render_lookup.get_template(name + '.tmpl')
            self.template = self.render_lookup.get_template('main.tmpl')

        def render(self):
            return self.template.render(title=TITLE, entries=ENTRIES)


try:
    import wheezy.template
except OSError:
    warnings.warn("Can't import wheezy.template, is it in your PYTHONPATH?")
    wheezy = None
if wheezy:
    # include this here so there's not a dependency on wheezy.html
    def wheezy_escape_html(s):
        return s.replace('&', '&amp;').replace('<', '&lt;').replace(
                         '>', '&gt;').replace('"', '&quot;')

    class Wheezy(TemplateLanguage):
        def __init__(self):
            self.engine = wheezy.template.Engine(
                    loader=wheezy.template.FileLoader([rel_dir('wheezy')]),
                    extensions=[wheezy.template.CoreExtension()])
            self.engine.global_vars.update({'h': wheezy_escape_html})

        def compile(self):
            for name in ('header', 'main', 'footer'):
                self.engine.remove(name + '.tmpl')
            for name in ('header', 'main', 'footer'):
                self.engine.get_template(name + '.tmpl')

        def setup_render(self):
            for name in ('header', 'main', 'footer'):
                self.engine.get_template(name + '.tmpl')
            self.template = self.engine.get_template('main.tmpl')

        def render(self):
            return self.template.render({'title': TITLE, 'entries': ENTRIES})


def hand_coded_filter(s):
    return (s.replace(u'&', u'&amp;')
             .replace(u'<', u'&lt;')
             .replace(u'>', u'&gt;')
             .replace(u"'", u'&#39;')
             .replace(u'"', u'&#34;'))

class HandCoded(TemplateLanguage):
    def compile(self):
        pass

    def header(self, _writes, filt, title):
        _writes((u'<html>\n<head>\n    <meta charset="UTF-8" />\n    <title>',
                 filt(title),
                 u'</title>\n</head>\n<body>\n<h1>',
                 filt(title),
                 u'</h1>\n\n'))

    def footer(self, _writes):
        _writes((u'\n</body>\n</html>',))

    def render(self, title=TITLE, entries=ENTRIES):
        filt = hand_coded_filter
        _output = []
        _writes = _output.extend

        self.header(_writes, filt, title)
        def paragraph(word):
            _writes((u'<p>This is ',
                     filt(word),
                     u' bunch of text just to test a whole bunch of text.</p>\n'))
        paragraph(u'a')
        paragraph(u'another')
        paragraph(u'yet another')
        _writes((u'\n',))
        for entry in entries:
            if entry.url:
                _writes((u'<h2><a href="',
                         filt(entry.url),
                         u'">',
                         filt(entry.title.title()),
                         u'</a></h2>\n'))
            else:
                _writes((u'<h2>',
                         filt(entry.title.title()),
                         u'</h2>\n'))
            _writes((entry.html_body, u'\n'))
        self.footer(_writes)

        return u''.join(_output)


def main():
    language_classes = [(name, cls) for name, cls in globals().items()
                        if isinstance(cls, type) and
                           issubclass(cls, TemplateLanguage) and
                           cls is not TemplateLanguage]

    results = []
    output = None
    for name, cls in language_classes:
        language = cls()
        timings = language.benchmark()
        results.append((name, timings['compile'], timings['render']))

        output_dir = rel_dir('output')
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        with open(os.path.join(output_dir, name.lower() + '.html'), 'wb') as f:
            language.setup_render()
            rendering = language.render().replace('\r\n', '\n')
            f.write(rendering.encode('utf-8'))
            if output is None:
                output = (name, rendering.strip())
            elif output[1] != rendering.strip():
                print 'ERROR: output from %s and %s differ' % (name, output[0])

    print 'Engine    compile (ms)  render (ms)'
    print '-----------------------------------'
    for name, compile_time, render_time in sorted(results, key=lambda r: r[2]):
        print '%-10s %11.3f %12.3f' % (name, compile_time * 1000, render_time * 1000)


if __name__ == '__main__':
    main()