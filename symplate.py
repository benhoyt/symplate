"""Symplate, the Simple pYthon teMPLATE renderer.

See README.md or https://github.com/benhoyt/symplate for documentation.

"""

from __future__ import with_statement

import os
import sys

__version__ = '0.9'


def html_filter(obj):
    """Default output filter. Escapes special HTML/XML characters in obj. If
    obj is None, return empty string. If obj is not a unicode string, convert
    it to a unicode string first.
    """
    if not isinstance(obj, unicode):
        if isinstance(obj, str):
            # if it's a byte string, do the best we can (try converting from
            # UTF-8, which is a superset of ASCII)
            obj = unicode(obj, 'utf-8')
        elif obj is None:
            return u''
        else:
            obj = unicode(obj)
    return (obj.replace(u'&', u'&amp;')
               .replace(u'<', u'&lt;')
               .replace(u'>', u'&gt;')
               .replace(u"'", u'&#39;')
               .replace(u'"', u'&#34;'))


class Error(Exception):
    """A Symplate template or syntax error."""

    def __init__(self, msg, line_num, text):
        self.msg = msg
        self.line_num = line_num
        self.text = text

    def __str__(self):
        line_msg = ', line %d' % self.line_num
        non_blanks = [l.strip() for l in self.text.splitlines() if l.strip()]
        if non_blanks:
            text_msg = ': ' + non_blanks[0]
            if len(non_blanks) > 1:
                text_msg += ' ...'
        else:
            text_msg = ''
        return self.msg + line_msg + text_msg

    def __repr__(self):
        text = self.text
        if len(text) > 50:
            text = text[:50] + '...'
        return 'symplate.Error(%r, %d, %r)' % (self.msg, self.line_num, text)


class Renderer(object):
    """Symplate renderer class. See __init__'s docs for more info."""

    def __init__(self, template_dir=None, output_dir=None, extension='.symp',
                 check_mtime=False, modify_path=True, preamble=''):
        """Initialize a Renderer instance.

        * template_dir: directory your Symplate source files are in, default
                        is current directory + 'symplates'
        * output_dir:   directory compiled template (.py) files should go
                        into, default is current directory + 'symplouts'
        * extension:    file extension for templates (set to '' if you want to
                        specify explictly when calling render)
        * check_mtime:  True means check template file's mtime on render(),
                        which is slower and usually only used for debugging
        * modify_path:  True means add output_dir/.. to sys.path for importing
                        compiled template
        * preamble:     extra code to include at top of compiled template,
                        such as imports
        """
        if template_dir is None:
            template_dir = os.path.abspath('symplates')
        self.template_dir = template_dir
        if output_dir is None:
            output_dir = os.path.abspath('symplouts')
        self.output_dir = output_dir
        self.extension = extension
        self.check_mtime = check_mtime
        self.modify_path = modify_path
        self.preamble = preamble
        self._module_cache = {}

    def get_default_filter(self, filename):
        """Return Python expression string to use as default filter for given
        template filename. Override this in subclasses to do fancy stuff like
        determine filter based on file extension.
        """
        return 'symplate.html_filter'

    def _compile_text(self, text, indent, outer_pieces, outer_i):
        """Compile the text parts of a template (the parts not inside {%...%}
        blocks) at given indent level and return list of Python source output
        strings.
        """
        output = []
        write = output.append

        def add_string(string):
            """Add a write(string) to the output."""
            if not string:
                return
            if len(string) > 50 and '\n' in string:
                # put long, multi-line text blocks inside raw """ strings
                # (but be sure to allow literal triple quotes to work
                chunks = string.split('"""')
                write('%s_write(' % indent)
                for i, chunk in enumerate(chunks):
                    if chunk:
                        write('ur"""%s""" ' % chunk)
                    if i + 1 < len(chunks):
                        write('u\'"""\' ')
                write(')\n')
            else:
                write('%s_write(%r)\n' % (indent, string))

        pieces = text.split('{{')
        for i, piece in enumerate(pieces):
            if i == 0:
                add_string(piece)
                continue

            expr_string = piece.split('}}')
            if len(expr_string) != 2:
                if len(expr_string) < 2:
                    msg = 'no }} at end of expression'
                else:
                    msg = 'more than one }} after expression'
                previous = '{{'.join(outer_pieces[:outer_i + 1] + pieces[:i])
                raise Error(msg, previous.count('\n') + 1, '{{' + piece)
            expr, string = expr_string
            expr = expr.strip()

            if expr.startswith('!'):
                expr = expr[1:].lstrip()
                write('%s_write(%s)\n' % (indent, expr))
            else:
                write('%s_write(filt(%s))\n' % (indent, expr))
            add_string(string)

        return output

    def _compile_string(self, template, filename=None):
        """Compile template string into Python source string."""
        def get_line_num(pieces, i):
            return '{%'.join(pieces[:i]).count('\n') + 1

        output = []
        write = output.append
        if filename:
            write('# Compiled by Symplate from: %s\n' % filename)
        write('# coding: utf-8\n\nimport symplate\n')
        write(self.preamble)

        indent = ''
        pieces = template.split('{%')
        in_template = False
        got_template = False
        for i, piece in enumerate(pieces):
            if i == 0:
                if piece.strip():
                    # output found before any {% ... %} blocks
                    raise Error('output must be inside {% template ... %}',
                                1, piece)
                continue

            code_text = piece.split('%}')
            if len(code_text) != 2:
                if len(code_text) < 2:
                    msg = 'no %} at end of block'
                else:
                    msg = 'more than one %} after block'
                raise Error(msg, get_line_num(pieces, i), '{%' + piece)

            code, text = code_text
            left_brackets_in_code = '{{' in code
            if left_brackets_in_code or '}}' in code:
                if left_brackets_in_code:
                    msg = '{{ not valid in code block'
                else:
                    msg = '}} not valid in code block'
                raise Error(msg, get_line_num(pieces, i), '{%' + piece)

            for line in code.splitlines():
                line = line.strip()
                if line.startswith(('template ', 'template\t')) or \
                        line == 'template':
                    if got_template:
                        raise Error("can't have multiple template directives",
                                    get_line_num(pieces, i), '{%' + piece)
                    write("""
def _render(_renderer, %s):
    filt = %s
    render = _renderer.render
    _output = []
    _write = _output.append

""" % (line[9:], self.get_default_filter(filename)))
                    if indent:
                        raise Error('{% template ... %} must be at top level',
                                    get_line_num(pieces, i), '{%' + piece)
                    indent += '    '
                    in_template = True
                    got_template = True

                elif line.startswith(('end ', 'end\t')) or line == 'end':
                    if not indent:
                        raise Error('extra {% end %}',
                                    get_line_num(pieces, i), '{%' + piece)
                    indent = indent[:-4]
                    if in_template and not indent:
                        write("\n    return u''.join(_output)\n")
                        in_template = False

                else:
                    end_colon = not line.startswith('#') and line.endswith(':')
                    if end_colon and line.startswith(
                            ('elif', 'else', 'except', 'finally')):
                        if not indent:
                            raise Error(
                                'dedent keyword not allowed at top level',
                                get_line_num(pieces, i), '{%' + piece)
                        indent = indent[:-4]
                    write(indent + line + '\n')
                    if end_colon:
                        indent += '    '

            # eat EOL immediately after a closing %}
            if text.startswith('\n'):
                text = text[1:]

            # ignore whitespace before {% template ... %}, if inside template
            # then write output
            if in_template or text.strip():
                text_output = self._compile_text(text, indent, pieces, i)
                if text_output and not in_template:
                    raise Error('output must be inside {% template ... %}',
                                get_line_num(pieces, i + 1), text)
                output.extend(text_output)

        if not got_template:
            lines = '{%'.join(pieces).splitlines() or '\n'
            raise Error('no {% template ... %} directive',
                        len(lines), lines[-1])
        if in_template and len(indent) != 4 or not in_template and indent:
            lines = '{%'.join(pieces).splitlines() or '\n'
            raise Error('template must end at top level',
                        len(lines), lines[-1])
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

    def compile(self, name):
        """Compile named template to .py in output directory."""
        names = self._get_filenames(name)

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

    def _get_module(self, name):
        """Import or compile and import named template and return module."""
        if self.modify_path:
            path_dir = os.path.abspath(os.path.join(self.output_dir, '..'))
            if path_dir not in sys.path:
                sys.path.insert(0, path_dir)

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
            module = __import__(names['module'], fromlist=[names['import']])
        except ImportError:
            self.compile(name)
            module = __import__(names['module'], fromlist=[names['import']])

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
    """Usage: symplate.py [-h] [options] action [name|dir|glob]

Actions:
  compile   compile given template, directory or glob (relative to
            TEMPLATE_DIR), default "*.symp\"
"""
    import fnmatch
    import optparse

    usage = main.__doc__.rstrip()
    version = 'Symplate ' + __version__
    parser = optparse.OptionParser(usage=usage, version=version)
    parser.add_option('-q', '--quiet', action='store_true',
                      help="don't print compiling information")
    parser.add_option('-n', '--non-recursive', action='store_true',
                      help="don't recurse into subdirectories")
    parser.add_option('-t', '--template-dir', default='symplates',
                      help='directory your Symplate files are in')
    parser.add_option('-o', '--output-dir', default='symplouts',
                      help='compiled template output directory, '
                           'default "%default"')
    parser.add_option('-p', '--preamble', default='',
                      help='template preamble (see docs), default ""')
    options, args = parser.parse_args()

    if len(args) <= 0:
        parser.error('no action given')
    action = args[0]
    if action != 'compile':
        # currently the only supported action
        parser.error('invalid action: ' + action)
    name = args[1] if len(args) > 1 else '*.symp'

    renderer = Renderer(template_dir=options.template_dir, extension='',
                        output_dir=options.output_dir,
                        preamble=options.preamble)

    # build list of filenames based on path or glob
    filenames = renderer._get_filenames(name)
    if os.path.isfile(filenames['symplate']):
        names = [name]
    else:
        if os.path.isdir(filenames['symplate']):
            path = filenames['symplate']
            pattern = '*.symp'
        else:
            path, pattern = os.path.split(filenames['symplate'])
            if not path:
                path = '.'
        names = []
        path = os.path.normpath(path)
        for root, dirs, files in os.walk(path):
            for f in files:
                if not fnmatch.fnmatch(f, pattern):
                    continue
                # mess around so we get a list of relatives template filenames
                # (os.path.relpath only available in Python 2.6+)
                abs_path = os.path.normpath(os.path.join(root, f))
                template_dir = os.path.normpath(options.template_dir)
                if not template_dir.endswith(os.sep):
                    template_dir += os.sep
                name = abs_path
                if name.startswith(template_dir):
                    name = name[len(template_dir):]
                names.append(name)
            if options.non_recursive:
                del dirs[:]

    for name in names:
        if not options.quiet:
            filenames = renderer._get_filenames(name)
            print 'compiling %s -> %s' % (filenames['symplate'],
                                          filenames['py'])
        renderer.compile(name)


if __name__ == '__main__':
    main()
