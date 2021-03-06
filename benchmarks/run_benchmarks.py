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
ENTRIES *= 10  # to give the render test a bit more to chew on


def rel_dir(dirname):
    """Return full directory name of dirname from this file's directory."""
    return os.path.abspath(os.path.join(os.path.dirname(__file__), dirname))


class TemplateLanguage(object):
    num_compiles = 10
    num_renders = 100
    version = ''

    def setup_compile(self):
        pass

    def compile(self):
        raise NotImplementedError

    def setup_render(self):
        pass

    def render(self):
        raise NotImplementedError

    def benchmark(self):
        self.setup_compile()
        compile_time = min(timeit.repeat(self.compile, number=self.num_compiles)) / float(self.num_compiles)
        self.setup_render()
        render_time = min(timeit.repeat(self.render, number=self.num_renders)) / float(self.num_renders)
        return (compile_time, render_time, self.version)


try:
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
    import symplate
except ImportError:
    warnings.warn("Can't import symplate, is it in your PYTHONPATH?")
    symplate = None
if symplate:
    class Symplate(TemplateLanguage):
        version = symplate.__version__

        def __init__(self):
            self.renderer = symplate.Renderer(rel_dir('symplate'))

        def compile(self):
            for name in ('header', 'main', 'footer'):
                self.renderer.compile(name)

        def render(self):
            return self.renderer.render('main', title=TITLE, entries=ENTRIES)


try:
    import Cheetah.Template as cheetah
    from Cheetah.Filters import WebSafe as cheetah_websafe
    from Cheetah import Version as cheetah_version
except ImportError:
    warnings.warn("Can't import Cheetah, is it in your PYTHONPATH?")
    cheetah = None
if cheetah:
    try:
        cheetah.checkFileMtime(False)
    except AttributeError:
        # Old Cheetah versions don't have checkFileMtime
        pass

    class Cheetah(TemplateLanguage):
        version = cheetah_version

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
            params = {'title': TITLE, 'entries': ENTRIES, 'template_dir': self.template_dir}
            return self.template(searchList=[params], filter=cheetah_websafe).respond()


try:
    import jinja2
except ImportError:
    warnings.warn("Can't import jinja2, is it in your PYTHONPATH?")
    jinja2 = None
if jinja2:
    class Jinja2(TemplateLanguage):
        version = jinja2.__version__

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
        version = mako.__version__

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
except ImportError:
    warnings.warn("Can't import wheezy.template, is it in your PYTHONPATH?")
    wheezy = None
if wheezy:
    # include this here so there's not a dependency on wheezy.html
    def wheezy_escape_html(s):
        return s.replace('&', '&amp;').replace('<', '&lt;').replace(
                         '>', '&gt;').replace('"', '&quot;')

    class Wheezy(TemplateLanguage):
        version = ''

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


try:
    import django
    import django.conf
    django.conf.settings.configure(TEMPLATE_DIRS=[rel_dir('django')])
    import django.template
    import django.template.loader
except ImportError:
    warnings.warn("Can't import django, is it in your PYTHONPATH?")
    django = None
if django:
    class Django(TemplateLanguage):
        version = django.get_version()

        def compile(self):
            django.template.loader.get_template('main.tmpl')

        def setup_render(self):
            self.template = django.template.loader.get_template('main.tmpl')

        def render(self):
            params = {'title': TITLE, 'entries': ENTRIES}
            return self.template.render(django.template.Context(params))


try:
    import bottle
except ImportError:
    warnings.warn("Can't import bottle, is it in your PYTHONPATH?")
    bottle = None
if bottle:
    class Bottle(TemplateLanguage):
        version = bottle.__version__

        def __init__(self):
            self.lookup = [rel_dir('bottle')]

        def compile(self):
            for name in ('header', 'main', 'footer'):
                template = bottle.SimpleTemplate(name=name + '.tmpl', lookup=self.lookup)
                template.co

        def setup_render(self):
            self.template = bottle.SimpleTemplate(name='main.tmpl', lookup=self.lookup)

        def render(self):
            return self.template.render(title=TITLE, entries=ENTRIES)


def hand_coded_filter(s):
    return (s.replace(u'&', u'&amp;')
             .replace(u'<', u'&lt;')
             .replace(u'>', u'&gt;')
             .replace(u"'", u'&#39;')
             .replace(u'"', u'&#34;'))

class HandCoded(TemplateLanguage):
    def compile(self):
        pass

    def header(self, title):
        filt = hand_coded_filter
        _output = []
        _writes = _output.extend
        _writes((u'<html>\n<head>\n    <meta charset="UTF-8" />\n    <title>',
                 filt(title),
                 u'</title>\n</head>\n<body>\n<h1>',
                 filt(title),
                 u'</h1>\n\n'))
        return u''.join(_output)

    def footer(self):
        return u'\n</body>\n</html>'

    def render(self, title=TITLE, entries=ENTRIES):
        filt = hand_coded_filter
        _output = []
        _write = _output.append
        _writes = _output.extend

        _write(self.header(title))
        def paragraph(word):
            _writes((u'<p>This is ',
                     filt(word),
                     u' bunch of text just to test a whole bunch of text.</p>\n'))
        paragraph(u'a')
        paragraph(u'another')
        paragraph(u'yet another')
        _write(u'\n')
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
        _write(self.footer())

        return u''.join(_output)

def main():
    language_classes = [(name, cls) for name, cls in globals().items()
                        if isinstance(cls, type) and
                           issubclass(cls, TemplateLanguage) and
                           cls is not TemplateLanguage]

    results = {}
    output = None
    for name, cls in language_classes:
        language = cls()
        results[name] = language.benchmark()

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

    # show compiler and render times (normalized to HandCoded render time)
    norm_time = results['HandCoded'][1]
    print 'engine             compile  render'
    print '----------------------------------'
    for name, timings in sorted(results.items(), key=lambda r: r[1][1]):
        compile_time, render_time, version = timings
        name_version = '%s %s' % (name, version)
        print '%-18s %7.3f %7.3f' % (
            name_version, compile_time / norm_time, render_time / norm_time)


if __name__ == '__main__':
    main()