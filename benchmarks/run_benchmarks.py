"""Run all benchmarks."""

import collections
import os
import sys
import timeit

import symplate

BlogEntry = collections.namedtuple('BlogEntry', 'title url html_body')

blog_entries = [
    BlogEntry('Sorry', '/sorry/', '<p>Sorry for the lack of updates.</p>'),
    BlogEntry('My life story', '/my-life-story/', '<p>Once upon a time...</p>'),
    BlogEntry(u'First \u201cpost\u201d', '/first-post/', '<p>This is the first post.</p>'),
]

class TemplateLanguage(object):
    def __init__(self):
        raise NotImplementedError

    def compile(self, name):
        raise NotImplementedError

    def render(self, name, *args, **kwargs):
        raise NotImplementedError

class Symplate(TemplateLanguage):
    def __init__(self):
        self.renderer = symplate.Renderer(
                template_dir=os.path.join(os.path.dirname(__file__), 'symplate'),
                output_dir=os.path.join(os.path.dirname(__file__), 'symplate_output'),
                modify_path=False)
        sys.path.insert(0, os.path.dirname(__file__))

    def compile(self, name):
        return self.renderer.compile(name)

    def render(self, name, *args, **kwargs):
        return self.renderer.render(name, *args, **kwargs)

def benchmark_language(language_class):
    timings = {}
    language = language_class()
    timings['compile'] = min(timeit.repeat(lambda: language.compile('main'), number=1000))
    timings['render'] = min(timeit.repeat(lambda: language.render('main', blog_entries), number=1000))
    return timings

def main():
    language_classes = [cls for name, cls in globals().items()
                        if isinstance(cls, type) and
                           issubclass(cls, TemplateLanguage) and
                           cls is not TemplateLanguage]
    for cls in language_classes:
        timings = benchmark_language(cls)
        print '%.20s %.1f %.1f' % (cls.__name__, timings['compile'] * 1000, timings['render'] * 1000)

if __name__ == '__main__':
    main()