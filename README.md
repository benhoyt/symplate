Symplate, the Simple pYthon teMPLATE renderer
=============================================

Symplate is the simplest, fastest, and most powerful Python templating
language. How's that for a sales pitch?

Seriously though, when I got frustrated with the complexities of
[Cheetah](http://www.cheetahtemplate.org/), I started wondering just how
simple a templating language could be.

Could you just write templates in straight Python? Not as bad as you'd think,
but pretty cumbersome: in templates, you really want string output to be the
default, whereas in Python, code is the default, and """strings have to wrapped
in quotes""". Plus, you don't get auto-escaping.

So I ended up with an ultra-simple Symplate-to-Python compilation process:

* `text` becomes `_write('text')`
* `{{ expr }}` becomes `_write(_filter(expr))`
* `{% code %}` becomes `code` at the correct indentation level
* indentation increases when a code line ends with a `:`, as in `{% for x in lst: %}`
* indentation decreases when you say `{% end %}`

That's about all there is to it. All the rest is detail or syntactic sugar.


Hats off to bottle.py
---------------------

Literally a few days after I wrote a draft version of Symplate, I saw a
reference to [Bottle](http://bottlepy.org) on Hacker News, and discovered the
author of that had almost exactly the same idea (no doubt some time earlier).
I thought of it independently, honest! Perhaps a good argument against
software patents...

Actually, one thing I stole from Bottle was its use of `!` to mean raw output.
It seemed cleaner than my initial idea of passing `raw=True` as a parameter to
the filter, as in `{{ foo, raw=True }}`.

And there are many other good templating languages available for Python now.
Not least of which is Mako, whose philosophy is very similar to Symplate's:
*Python is a great scripting language. Don't reinvent the wheel... your
templates can handle it!*


Basic usage
-----------

Let's start with a simple example that uses more or less all the features of
Symplate. Our main template is `blog.symp`:

    {% template entries, title='My Blog' %}
    {% include 'inc/header', title %}
    <h1>This is {{ title }}</h1>
    {% for entry in entries: %}
        <h2><a href="{{ entry.url }}">{{ entry.title.title() }}</a></h2>
        {{ !entry.html_body }}
    {% end %}
    </ul>
    {% include 'inc/footer' %}

This is Python, so everything's explicit. We explicitly specify the parameters
this template takes in the `{% template ... %}` line, including the default
parameter `title`. The arguments passed to included sub-templates are
specified explicitly (no yucky setting of globals for includes).

Note that `entry.html_body` contains pre-rendered HTML, so this expression is
prefixed with `!`, meaning output a raw, unescaped string.

Then `inc/header.symp` looks like this:

    {% template title %}
    <html>
    <head>
        <meta charset="UTF-8" />
        <title>{{ title }}</title>
    </head>
    <body>

And `inc/footer.symp` is of course:

    {% template %}
    </body>
    </html>

To compile and render the main blog template in one fell swoop, set `entries`
to a list of blog entries with the `url`, `title`, and `html_body` attributes,
and you're away:

    output = symplate.render('blog', entries, title="Ben's Blog")


Non-default Rendererer
======================

Calling `symplate.render()` directly uses the default `symplate.Renderer()`
instance. You may well want to use your own to specify a different template or
output directory, or to turn on checking of template file mtimes for
debugging. For example:

    debug = os.getenv('BLOG_DEBUG') == 'true'
    renderer = symplate.Renderer(output_dir='out', check_mtime=debug)

    def homepage():
        entries = load_blog_entries()
        return renderer.render('blog', entries, title="Ben's Blog")

See `Renderer.__init__`'s docstring or type `help(symplate.Renderer)` at a
Python prompt for more info.


Compiled Python output
======================

Symplate is a [leaky abstraction](http://www.joelonsoftware.com/articles/LeakyAbstractions.html),
but is somewhat proud of that fact. I already know Python well, so my goal was
to be as close to Python as possible -- I don't want to learn another language
just to produce some HTML.

In any case, you're encouraged to look the compiled Python output produced by
the Symplate compiler. You might be surprised how clean it looks. Symplate
tries to make the compiled template look much like it would if you were
writing it by hand -- for example, short strings are output as `'shortstr'`,
and long, multi-line strings as """long, multi-line strings""".

The `blog.symp` example above produces this in `blog.py`:

    import symplate

    def render(_renderer, entries, title='My Blog'):
        _output = []
        _write = _output.append
        _filter = symplate.html_filter

        _write(_renderer.render('inc/header', title))
        _write(u'<h1>This is ')
        _write(_filter(title))
        _write(u'</h1>\n')
        for entry in entries:
            _write(u'    <h2><a href="')
            _write(_filter(entry.url))
            _write(u'">')
            _write(_filter(entry.title.title()))
            _write(u'</a></h2>\n    ')
            _write(entry.html_body)
            _write(u'\n')
        _write(u'</ul>\n')
        _write(_renderer.render('inc/footer'))

        return u''.join(_output)

Basic Symplate syntax errors like mismatched `{%`'s are raised as
`symplate.Error`s when the template is compiled. However, most Python
expressions are copied directly to the Python output, so you only get a Python
SyntaxError when the compiled template is imported at render time. (Yes, this
is a minor drawback of Symplate's KISS approach.)


Directives
==========

The only directives or keywords in Symplate are `template`, `include`, and
`end`. Oh, and "colon at the end of a code line".

`{% template [args] %}` must appear at the start of a template before any
output. `args` is the argument specification including positional and
keyword/default arguments, just as if it were a function definition. In fact,
it is -- `{% template [args] %}` gets compiled to:

    def render(_renderer, args):
        ...

`{% include name[, args] %}` renders the template with the given name and
arguments and writes the result to the output. This is exactly equivalent to
the more clumsy:

    {{ !_renderer.render(name, args) }}

`{% end [...] %}` ends a code indentation block. All it does is reduce the
indentation level in the compiled Python output. The `...` is optional, and
acts as a comment, so you can say `{% end for %}` or `{% end if %}` if you
like.

A `:` (colon) at the end of a code block starts a code indentation block, just
like in Python. So you've got to match your `{% ...: %}`s with your
`{% end %}`s.


Filters
-------

### The default filter

The default filter used by `{{ ... }}` output expressions is `html_filter`,
which converts non-string objects to unicode and escapes HTML/XML special
characters. It escapes `&`, `<`, `>`, `'`, and `"`, so it's good for both HTML
content as well as attribute values.

For example, `render('foo.tmpl', thing='A & B', title="Symplate's simple")` on
this template:

    Thing is <b>{{ thing }}</b>.
    <img src='logo.png' title='{{ title }}'>

Would produce the output:

    Thing is <b>A &amp; B</b>.
    <img src='logo.png' title='Symplate&#39;s simple'>

### Outputting raw strings

To output a raw or pre-escaped string, prefix the output expression with `!`,
For example `{{ !html_block }}` will write `html_block` directly to the
output, meaning it must be a unicode string or a pure-ASCII byte string.

### Setting the filter

To set the current filter, just say `{% _filter = filter_function %}`.
`_filter` is simply a local variable in the compiled template, and it should
be set to a function which takes a single argument and returns a unicode
string.

The expression inside a `{{ ... }}` is passed directly to the current
`_filter` function, so you can pass other arguments to custom filters. For
example:

    {% _filter = json.dumps %}
    {{ obj, indent=4, sort_keys=True }}

### Changing the default filter

You can change the default filter by subclassing `Renderer` and overriding
`get_default_filter()`. It's a function which is passed the template filename
as its single argument, so you can use the filename or extension to do clever
things if you want. By default it simply returns the string
`'symplate.html_filter'`, but you could do something like this:

    class SmartRenderer(symplate.Renderer):
        def __init__(self, *args, **kwargs):
            super(SmartRenderer, self).__init__(*args, **kwargs)
            self.preamble += 'import json\n'

        def get_default_filter(self, filename):
            base, ext = os.path.splitext(filename)
            if ext.lower() == '.js':
                return 'json.dumps'
            else:
                return 'symplate.html_filter'

Note the modified `premable` so the compiled template has the `json` module
available.


Unicode handling
----------------

Symplate templates have full support for Unicode. The template files are
always encoded in UTF-8, and internally Symplate builds the template as
unicode.

`render()` always returns a unicode string, and it's best to pass unicode
strings as arguments to `render()`, but you can also pass byte strings encoded
as UTF-8 -- the default filter `html_filter` will handle both.


Comments
--------

Because `{% ... %}` blocks are simply copied to the compiled template as
Python code, there's no special handling for comments -- just use standard
Python `#` comments inside code blocks:

    {% # This is a comment. %}
    {% # Multi-line comments
       # work fine too. %}
    {{ foo # DON'T COMMENT INSIDE OUTPUT EXPRESSIONS }}

One quirk is that Symplate determines when to indent the Python output based
on the `:` character being at the end of the line, so you can't add a comment
after the colon that begins an indentation block:

    {% for element in lst: # THIS WON'T WORK %}


Outputting a literal {{, }}, {%, or %}
--------------------------------------

You can't include `{{`, `}}`, `{%`, or `%}` anywhere inside an output
expression or code block. To output one of these two-character strings
literally, use Python's string literal concatenation so that the two special
characters are separated.

For example, this will output a single `{{`:

    {{ '{' '{' }}

If you find yourself needing this a lot (for instance in writing a template
about templates), you could shortcut and name it at the top of your template:

    {% LB, RB = '{' '{', '}' '}' %}
    {{LB}}one{{RB}}
    {{LB}}two{{RB}}
    {{LB}}three{{RB}}


Command line usage
------------------

`symplate.py` can also be run as a command-line script. This is currently only
useful for pre-compiling one or more templates, which might be useful in a
constrained deployment environment where you can only upload Python code, and
not write to the file system.

Simply specify your template directory and output directory and it'll compile
all your templates to Python code. Straight from the command line help:

    Usage: symplate.py [-h] [options] action [name|dir|glob]

    Actions:
      compile   compile given template, directory or glob (relative to
                TEMPLATE_DIR), default "*.symp"

    Options:
      --version             show program's version number and exit
      -h, --help            show this help message and exit
      -q, --quiet           don't print compiling information
      -n, --non-recursive   don't recurse into subdirectories
      -t TEMPLATE_DIR, --template-dir=TEMPLATE_DIR
                            directory your Symplate files are in
      -o OUTPUT_DIR, --output-dir=OUTPUT_DIR
                            compiled template output directory, default
                            "symplouts"
      -p PREAMBLE, --preamble=PREAMBLE
                            template preamble (see docs), default ""


Flames, comments, bug reports
-----------------------------

Please send flames, comments, and questions about Symplate to Ben Hoyt:

http://benhoyt.com/

File bug reports or feature requests at the GitHub project page:

https://github.com/benhoyt/symplate
