"""Symplate, the Simple pYthon teMPLATE renderer.

See README.md or https://github.com/benhoyt/symplate for documentation.

"""

from __future__ import with_statement

import os
import sys

__version__ = '0.9'


def html_filter(s):
    """Escape special HTML/XML characters in given ASCII or unicode string
    (this is the default output filter in templates).
    """
    # slight performance boost by feeding correct string type into replace()
    if isinstance(s, unicode):
        return (s.replace(u'&', u'&amp;')
                 .replace(u'<', u'&lt;')
                 .replace(u'>', u'&gt;')
                 .replace(u"'", u'&#39;')
                 .replace(u'"', u'&#34;'))
    else:
        return (s.replace('&', '&amp;')
                 .replace('<', '&lt;')
                 .replace('>', '&gt;')
                 .replace("'", '&#39;')
                 .replace('"', '&#34;'))


class Error(Exception):
    """A Symplate template or syntax error."""

    def __init__(self, msg, template, line_num):
        super(Error, self).__init__(msg, template, line_num)
        self.msg = msg
        self.template = template
        self.line_num = line_num
        lines = template.splitlines()
        if 0 <= line_num - 1 < len(lines):
            self.line = lines[line_num - 1]
        else:
            self.line = ''

    def __str__(self):
        return '%s, line %d: %s' % (self.msg, self.line_num, self.line.strip())

    def __repr__(self):
        return 'symplate.Error<%r>' % str(self)


class Renderer(object):
    """Symplate renderer class. See __init__'s docs for more info."""

    def __init__(self, template_dir, output_dir=None, extension='.symp',
                 check_mtime=False, modify_path=True, preamble=''):
        """Initialize a Renderer instance.

        * template_dir: directory your Symplate source files are in (the only
                        required argument)
        * output_dir:   directory compiled template (.py) files should go
                        into, default is {template_dir}/../symplouts
        * extension:    file extension for templates (set to '' if you want to
                        specify explictly when calling render)
        * check_mtime:  True means check template file's mtime on render(),
                        which is slower and usually only used for debugging
        * modify_path:  True means add output_dir/.. to sys.path for importing
                        compiled template
        * preamble:     extra code to include at top of compiled template,
                        such as imports
        """
        self.template_dir = os.path.abspath(template_dir)
        if output_dir is None:
            output_dir = os.path.abspath(os.path.join(self.template_dir, '..',
                                                      'symplouts'))
        self.output_dir = output_dir
        self.extension = extension
        self.check_mtime = check_mtime
        self.preamble = preamble
        self._module_cache = {}

        if modify_path:
            path_dir = os.path.abspath(os.path.join(output_dir, '..'))
            sys.path.insert(0, path_dir)

    def get_default_filter(self, filename):
        """Return Python expression string to use as default filter for given
        template filename. Override this in subclasses to do fancy stuff like
        determine filter based on file extension.
        """
        return 'symplate.html_filter'

    def _compile_text(self, text, indent, template, line_num):
        """Compile the text parts of a template (the parts not inside {%...%}
        blocks) at given indent level and return list of Python source output
        lines.
        """
        writes = []
        add_write = writes.append

        def add_string(string):
            """Add a write(string) to the output."""
            if not string:
                return
            if len(string) > 50 and '\n' in string:
                # put long, multi-line text blocks inside raw """ strings
                # (but be sure to allow literal triple quotes to work
                chunks = string.split('"""')
                output = []
                for i, chunk in enumerate(chunks):
                    if chunk:
                        output.append('ur"""%s""" ' % chunk)
                    if i + 1 < len(chunks):
                        output.append('u\'"""\' ')
                add_write(''.join(output))
            else:
                add_write(repr(string))

        pieces = text.split('{{')
        for i, piece in enumerate(pieces):
            if i == 0:
                add_string(piece)
                line_num += piece.count('\n')
                continue

            expr_string = piece.split('}}')
            if len(expr_string) != 2:
                if len(expr_string) < 2:
                    msg = 'no }} at end of expression'
                else:
                    msg = 'more than one }} after expression'
                raise Error(msg, template, line_num)
            expr, string = expr_string
            expr = expr.strip()

            if expr.startswith('!'):
                expr = expr[1:].lstrip()
                if expr:
                    add_write(expr)
            elif expr:
                add_write('filt(%s)' % expr)
            add_string(string)

            line_num += piece.count('\n')

        output = []
        if writes:
            output.append(indent + '_writes((\n')
            output.extend('%s    %s,\n' % (indent, w) for w in writes)
            output.append(indent + '))\n')

        return output

    def _compile_string(self, template, filename=None):
        """Compile template string into Python source string."""
        def error(msg):
            raise Error(msg, template, line_num)

        output = []
        write = output.append
        if filename:
            write('# Compiled by Symplate from: %s\n' % filename)
        write('# coding: utf-8\n\nimport symplate\n')
        write(self.preamble)

        indent = ''
        in_template = False
        got_template = False
        line_num = 1
        pieces = template.split('{%')
        for i, piece in enumerate(pieces):
            if i == 0:
                if piece.strip():
                    # output found before any {% ... %} blocks
                    error('output must be inside {% template ... %}')
                line_num += piece.count('\n')
                continue

            code_text = piece.split('%}')
            if len(code_text) != 2:
                if len(code_text) < 2:
                    error('no %} at end of block')
                else:
                    error('more than one %} after block')

            code, text = code_text
            left_brackets_in_code = '{{' in code
            if left_brackets_in_code or '}}' in code:
                brackets = '{{' if left_brackets_in_code else '}}'
                error('%s not valid in code block' % brackets)

            for line_with_end in code.splitlines(True):
                line = line_with_end.strip()
                if line.startswith(('template ', 'template\t')) or \
                        line == 'template':
                    if got_template:
                        error("can't have multiple template directives")
                    write("""
def _render(_renderer, %s):
    filt = %s
    render = _renderer.render
    _output = []
    _writes = _output.extend

""" % (line[9:], self.get_default_filter(filename)))
                    if indent:
                        error('{% template ... %} must be at top level')
                    indent += '    '
                    in_template = True
                    got_template = True

                elif line.startswith(('end ', 'end\t')) or line == 'end':
                    if not indent:
                        error('extra {% end %}')
                    indent = indent[:-4]
                    if in_template and not indent:
                        write("\n    return u''.join(_output)\n")
                        in_template = False

                else:
                    end_colon = not line.startswith('#') and line.endswith(':')
                    if end_colon and line.startswith(
                            ('elif', 'else', 'except', 'finally')):
                        if not indent:
                            error('dedent keyword not allowed at top level')
                        indent = indent[:-4]
                    write(indent + line + '\n')
                    if end_colon:
                        indent += '    '

                line_num += line_with_end.count('\n')

            # eat EOL immediately after a closing %}
            if text.startswith('\n'):
                text = text[1:]
                line_num += 1
            # eat spaces and tabs at beginning of {% line
            text = text.rstrip(' \t')

            # ignore whitespace before {% template ... %}, if inside template
            # then write output
            if in_template or text.strip():
                text_output = self._compile_text(text, indent, template,
                                                 line_num)
                if text_output and not in_template:
                    error('output must be inside {% template ... %}')
                output.extend(text_output)
            line_num += text.count('\n')

        if not got_template:
            error('no {% template ... %} directive')
        if in_template and len(indent) != 4 or not in_template and indent:
            error('template must end at top level')
        if in_template:
            write("\n    return u''.join(_output)\n")

        return ''.join(output)

    def _get_filenames(self, name):
        """Helper function to get dict with the various filenames for given
        template name.
        """
        symplate = os.path.join(self.template_dir, name + self.extension)
        import_, ext = os.path.splitext(name)
        py = os.path.join(self.output_dir, import_ + '.py')
        import_ = import_.replace('/', '.').replace('\\', '.')
        rel_output_dir = self.output_dir.replace('\\', '/').split('/')[-1]
        module = rel_output_dir + '.' + import_
        names = {
            'symplate': symplate,
            'import': import_,
            'py': py,
            'module': module,
        }
        return names

    def _make_output_dir(self, output_dir):
        """Create an output directories along with its __init__.py."""
        if os.path.exists(output_dir):
            return
        os.mkdir(output_dir)
        init_py_name = os.path.join(output_dir, '__init__.py')
        with open(init_py_name, 'w') as f:
            f.write('')

    def compile(self, name, verbose=False):
        """Compile named template to .py in output directory."""
        names = self._get_filenames(name)
        if verbose:
            print 'compiling %s -> %s' % (names['symplate'], names['py'])

        with open(names['symplate']) as f:
            template = unicode(f.read(), 'utf-8')
        symplate_name = os.path.abspath(names['symplate'])
        py_source = self._compile_string(template, filename=symplate_name)

        # create intermediate and final output directories with __init__.py
        self._make_output_dir(self.output_dir)
        rel_output_dir = os.path.normpath(os.path.dirname(name))
        dir_names = rel_output_dir.split(os.sep)
        for i in range(len(dir_names)):
            cur_output_dir = os.path.join(self.output_dir, *dir_names[:i + 1])
            self._make_output_dir(cur_output_dir)

        with open(names['py'], 'w') as f:
            f.write(py_source.encode('utf-8'))

        # ensure .pyc and .pyo are gone so it doesn't get reloaded from them
        def remove_if_exists(filename):
            try:
                os.remove(filename)
            except OSError:
                pass
        py_basename = os.path.splitext(names['py'])[0]
        remove_if_exists(py_basename + '.pyc')
        remove_if_exists(py_basename + '.pyo')

    def compile_all(self, recursive=True, verbose=False):
        """Compile all templates in template_dir to .py files."""
        for root, dirs, files in os.walk(self.template_dir):
            for base_name in files:
                if not base_name.endswith(self.extension):
                    continue
                full_name = os.path.join(root, base_name)
                prefix_len = len(self.template_dir)
                if not self.template_dir.endswith(os.sep):
                    prefix_len += 1
                name = full_name[prefix_len:]
                if self.extension:
                    name = name[:-len(self.extension)]
                self.compile(name, verbose=verbose)

            if not recursive:
                dirs[:] = []

    def _get_module(self, name):
        """Import or compile and import named template and return module."""
        names = self._get_filenames(name)
        if self.check_mtime:
            # compile the template source to .py if it has changed
            try:
                py_mtime = os.path.getmtime(names['py'])
            except OSError:
                py_mtime = 0
            if os.path.getmtime(names['symplate']) > py_mtime:
                self.compile(name)
                # .py changed, ensure module is reloaded when imported below
                if names['module'] in sys.modules:
                    sys.modules.pop(names['module'])

        # try to import the compiled template; if it doesn't exist (it's never
        # been compiled), compile it and then re-import
        try:
            module = __import__(names['module'], globals(), locals(),
                                [names['import']])
        except ImportError:
            self.compile(name)
            module = __import__(names['module'], globals(), locals(),
                                [names['import']])

        return module

    def render(self, name, *args, **kwargs):
        """Render named template with given positional and keyword args."""
        if name in self._module_cache:
            module = self._module_cache[name]
        else:
            module = self._get_module(name)
            # only store in module cache if we're not checking mtimes
            if not self.check_mtime:
                self._module_cache[name] = module
        return module._render(self, *args, **kwargs)


def main():
    """Usage: symplate.py [-h] [options] template_dir [template_names]

Compile templates in specified template_dir, or all templates if
template_names not given
"""
    import optparse

    usage = main.__doc__.rstrip()
    version = 'Symplate ' + __version__
    parser = optparse.OptionParser(usage=usage, version=version)
    parser.add_option('-o', '--output-dir',
                      help='compiled template output directory, '
                           'default {template_dir}/../symplouts')
    parser.add_option('-e', '--extension', default='.symp',
                      help='file extension for templates, default %default')
    parser.add_option('-p', '--preamble', default='',
                      help='template preamble (see docs), default ""')
    parser.add_option('-q', '--quiet', action='store_true',
                      help="don't print what we're doing")
    parser.add_option('-n', '--non-recursive', action='store_true',
                      help="don't recurse into subdirectories")
    options, args = parser.parse_args()

    if len(args) <= 0:
        parser.error('no template_dir given')
    template_dir = args[0]
    template_names = args[1:]

    extension = options.extension
    if not extension.startswith('.'):
        extension = '.' + extension
    renderer = Renderer(template_dir, output_dir=options.output_dir,
                        extension=extension, preamble=options.preamble)

    if template_names:
        for name in template_names:
            renderer.compile(name, verbose=not options.quiet)
    else:
        template_names = renderer.compile_all(
            recursive=not options.non_recursive,
            verbose=not options.quiet)


if __name__ == '__main__':
    main()
