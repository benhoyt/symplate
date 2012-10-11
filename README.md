Symplate, the Simple pYthon teMPLATE renderer
=============================================

Symplate is a very simple and very fast Python template language.

* [Background](#background)
* [FAQ](#faq) -- [Who](#who-uses-symplate) | [Why](#why-use-symplate) | [Performance](#isnt-worrying-about-performance-silly)
* [Basic usage](#basic-usage)
* [Compiled Python output](#compiled-python-output)
* [Syntax](#syntax) -- [Directives](#directives) | [Whitespace](#whitespace-handling) | [Comments](#comments) | [Literals](#outputting-a-literal----or-)
* [Filters](#filters) -- [Default](#the-default-filter) | [Raw](#outputting-raw-strings) | [Setting](#setting-the-filter) | [Overriding](#overriding-the-default-filter)
* [Including sub-templates](#including-sub-templates)
* [Customizing Renderer](#customizing-renderer)
* [Unicode handling](#unicode-handling)
* [Command line usage](#command-line-usage)
* [Meta](#meta) -- [Bottle](#hats-off-to-bottlepy) | [To-do](#to-do) | [Feedback](#flames-comments-bug-reports)


Background
----------

When I got frustrated with the complexities and slow rendering speed of
[Cheetah](http://www.cheetahtemplate.org/), I started wondering just how
simple a template language could be.

You could write templates in pure Python, but that's somewhat painful -- code
and text are hard to intersperse, and you don't get auto-escaping. But why not
a KISS template-to-Python translator? Enter Symplate:

* `text` becomes `_write('text')`
* `{{ expr }}` becomes `_write(filt(expr))`
* `{% code %}` becomes `code` at the correct indentation level
* indentation increases when a code line ends with a colon, as in
  `{% for x in lst: %}`
* indentation decreases when you say `{% end %}`

That's about all there is to it. All the rest is [detail](#directives).


FAQ
---

### Who uses Symplate?

Only me ... so far. It started as my experiment. That said, Symplate is now a
proper library, and fairly well tested. I also "ported" my
[GiftyWeddings.com](http://giftyweddings.com/) website from Cheetah to
Symplate, and it's working very well.

### Why use Symplate?

If you care about **raw performance** or **simplicity of implementation**,
Symplate might be for you. I care about both, and I haven't needed some of the
extra features other systems provide, such as sandboxed execution and template
inheritance. If you want a Porsche, use Symplate. If you'd prefer a Volvo or
BMW, I'd recommend [Jinja2](http://jinja.pocoo.org/docs/) or
[Mako](http://www.makotemplates.org/).

Symplate is dead simple: a couple of pages of code translate your templates to
Python `.py` files, and `render()` imports and executes the compiled output.

Symplate's also about as fast as a pure-Python template language can be.
Partly *because* it's simple, it produces Python code as tight as you'd write
it by hand.

### Isn't worrying about performance silly?

Yes, I know, [worrying about template performance is
silly](http://www.codeirony.com/?p=9). *Some of the time.* But when you're
caching everything to avoid database requests, and your "business logic" is
pretty tight, template rendering is all that's left. And Cheetah (not to
mention Django!) are particlarly slow.

If you're running a large-scale website and you're caching things so that
template rendering *is* your bottleneck (yes, I've been there) ... then if you
can take your render times down from 100ms to 20ms, you can run your website
on 1/5th the number of servers.

So how fast is Symplate? As mentioned, it's about as fast as you can hand-code
Python. Here's the Symplate benchmark showing compile and render times for
some of the fast or popular template languages.

Times are normalized to the HandCoded render time:

    engine             compile  render
    ----------------------------------
    HandCoded            0.001   1.000
    Symplate 0.9        11.900   1.138
    Wheezy              29.604   1.349
    Bottle 0.11.rc1     10.296   2.575
    Mako 0.7.2          60.189   3.876
    Jinja2 2.6          68.179   5.581
    Cheetah 2.4.4      121.454   5.919
    Django 1.3.3         7.698  20.506


Basic usage
-----------

Let's start with a simple example that uses more or less all the features of
Symplate. Our main template file is `blog.symp`:

    {% template entries, title='My Blog' %}
    {{ !render('inc/header', title) }}
    <h1>This is {{ title }}</h1>
    {% for entry in entries: %}
        <h2><a href="{{ entry.url }}">{{ entry.title.title() }}</a></h2>
        {{ !entry.html_body }}
    {% end for %}
    </ul>
    {{ !render('inc/footer') }}

In true Python style, everything's explicit. We explicitly specify the
parameters the template takes in the `{% template ... %}` line, including the
default parameter `title`.

For simplicity, there's no special "include" directive -- you just [`render()`
a sub-template](#including-sub-templates) -- usually with the `!` prefix to
mean don't filter the rendered output.

In this example, `entry.html_body` contains pre-rendered HTML, so this
expression is also prefixed with `!` -- it will output the HTML body as a
[raw, unescaped string](#outputting-raw-strings).

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

```python
renderer = symplate.Renderer(template_dir)

def homepage():
    return renderer.render('blog', entries, title="Ben's Blog")
```

You can [customize your Renderer](#customizing-renderer) to specify a
different output directory, or to turn on checking of template file mtimes for
debugging. For example:

```python
renderer = symplate.Renderer(template_dir, output_dir='out',
                             check_mtime=settings.DEBUG)

def homepage():
    entries = load_blog_entries()
    return renderer.render('blog', entries, title="Ben's Blog")
```

Compiled Python output
----------------------

Symplate is a [leaky
abstraction](http://www.joelonsoftware.com/articles/LeakyAbstractions.html),
but is somewhat proud of that fact. I already knew Python well, so my goal was
to be as close to Python as possible -- I don't want to learn another language
just to produce some escaped HTML.

In any case, you're encouraged to look at the compiled Python output produced
by the Symplate compiler (usually placed in a `symplouts` directory at the
same level as your template directory).

You might be surprised how simple the compiled output is. Symplate tries to
make the compiled template look much like it would if you were writing it by
hand -- for example, short strings are output as `'shortstr'`, and long,
multi-line strings as `"""long, multi-line strings"""`.

The `blog.symp` example above produces this in `blog.py`:

```python
import symplate

def _render(_renderer, entries, title='My Blog'):
    filt = symplate.html_filter
    render = _renderer.render
    _output = []
    _writes = _output.extend

    _writes((
        render('inc/header', title),
        u'\n<h1>This is ',
        filt(title),
        u'</h1>\n',
    ))
    for entry in entries:
        _writes((
            u'    <h2><a href="',
            filt(entry.url),
            u'">',
            filt(entry.title.title()),
            u'</a></h2>\n    ',
            entry.html_body,
            u'\n',
        ))
    _writes((
        u'</ul>\n',
        render('inc/footer'),
        u'\n',
    ))

    return u''.join(_output)
```

As you can see, apart from a tiny premable, it's about as fast and direct as
it could possibly be in pure Python.

Basic Symplate syntax errors like mismatched `{%`'s are raised as
`symplate.Error`s when the template is compiled. However, most Python
expressions are copied directly to the Python output, so you'll only get a
Python `SyntaxError` when the compiled template is imported at render time.

(Yes, this is a minor drawback of Symplate's KISS approach. However, because
Symplate is such a direct mapping to Python, it's usually easy to find errors
in your templates.)


Syntax
------

Symplate has very little syntax of its own, but here's what you need to know:

### Directives

The only directives or keywords in Symplate are `template` and `end`. Oh, and
"colon at the end of a code line".

`{% template [args] %}` must appear at the start of a template before any
output. `args` is the argument specification including positional and
keyword/default arguments, just as if it were a function definition. In fact,
it is -- `{% template [args] %}` gets compiled to 
`def render(_renderer, args): ...`.

If you need to import other modules, do so at the top of your template, above
the `template` directive (just like how in Python you import before writing
code).

`{% end [...] %}` ends a code indentation block. All it does is reduce the
indentation level in the compiled Python output. The `...` is optional, and
acts as a comment, so you can say `{% end for %}` or `{% end if %}` if you
like.

A `:` (colon) at the end of a code block starts a code indentation block, just
like in Python. However, there's a special case for the `elif`, `else`,
`except` and `finally` keywords -- they dedent for the line the keyword is on,
and then indent again (just like you would when writing Python).

### Whitespace handling

Symplate has some very simple rules for whitespace handling. The idea is to do
what's normal for the common case, but you can always insert extra whitespace
to get what you want if this doesn't suit. The rules are:

* Eat spaces and tabs at the beginning of `{% ... %}` lines
* Eat newline character immediately after a closing `%}`, except when the code
  block is "inline"
* All other whitespace Symplate leaves alone

An example which shows all this in action is:

    {% template %}
    <ul>
    {% for i in range(10): %}
        {% if i % 2 == 0: %}
        <li>{% if i == 0: %}zero{% else: %}{{ i }}{% end if %}</li>
        {% end if %}
    {% end for %}
    </ul>

The above template produces the following output.

    <ul>
        <li>zero</li>
        <li>2</li>
        <li>4</li>
        <li>6</li>
        <li>8</li>
    </ul>


### Comments

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

    {% for element in lst: # DON'T DO THIS %}

### Outputting a literal {{, }}, {%, or %}

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


Filters
-------

### The default filter

The default filter used by `{{ ... }}` output expressions is `html_filter`,
which converts its argument to unicode and then escapes HTML/XML special
characters. It escapes `&`, `<`, `>`, `'`, and `"`, so it's good for both HTML
content as well as attribute values.

`html_filter` converts byte strings to unicode using UTF-8. It converts other
non-string objects simply using `unicode(obj)`, except for `None`, for which
it returns an empty string (almost always what you want).

For example, `render('test', thing='A & B', title="Symplate's simple")` on
this template:

    Thing is <b>{{ thing }}</b>.
    <img src='logo.png' title='{{ title }}'>
    {{ 1234 }}{{ None }}{{ '\xe2\x80\x99' }}

Would produce the following output:

    Thing is <b>A &amp; B</b>.
    <img src='logo.png' title='Symplate&#39;s simple'>
    1234’

### Outputting raw strings

To output a raw or pre-escaped string, prefix the output expression with `!`.
For example `{{ !html_string }}` will write `html_string` directly to the
output, meaning it must be a unicode string or a pure-ASCII byte string.

### Setting the filter

To set the current filter, just say `{% filt = filter_function %}`. `filt` is
simply a local variable in the compiled template, and it should be set to a
function which takes a single argument and returns a unicode or ASCII string.

The expression inside a `{{ ... }}` is passed directly to the current `filt`
function, so you can pass other arguments to custom filters. For example:

    {% filt = json.dumps %}
    {{ obj, indent=4, sort_keys=True }}

If you need to change back to the default filter (`html_filter`), just say:

    {% filt = symplate.html_filter %}

The other handy built-in filter is `symplate.text_filter`, which handles
objects the same way as `html_filter`, but doesn't HTML-escape the result.

### Overriding the default filter

You can override the default filter by passing `Renderer` the `default_filter`
argument. If this is a string, it's used directly for setting the filter, as
per the above:

```python
# this default filter will make everything uppercase
renderer = symplate.Renderer(default_filter='lambda s: s.upper()')
```

If it's not a string, it must be a function which takes a single `filename`
(the template filename) as its argument. This is useful when, for example, you
want to determine the default filter based on the template's file extension.
A simple example:

```python
# this default filter will use json.dumps() for .js.symp files and the
# normal HTML filter for other files
def get_default_filter(self, filename):
    if filename.lower().endswith('.js.symp'):
        return 'json.dumps'
    else:
        return 'symplate.html_filter'

renderer = symplate.Renderer(default_filter=get_default_filter,
                             preamble='import json\n')
```

Note the modified `premable` so the compiled template has the `json` module
available.


Including sub-templates
-----------------------

Symplate has no literal "include" directive. You simply call `render` in an
output expression, like this:

    {{ !render('sub_template_name', *args, **kwargs) }}

`render` inside templates is set to the current Renderer instance's `render`
function, so it uses the settings you expect. Note that you almost always use
the `!` raw-output prefix, so that the rendered sub-template isn't
HTML-escaped further.

The arguments passed to `render()`ed sub-templates are specified explicitly,
so there's no yucky setting of globals when rendering included templates.

Symplate doesn't currently support template inheritance -- it prefers
"composition over inheritance", if you will. For instance, if your header
template has an ad in its sidebar that can vary by page, you could say:

    {{ !render('header', title='My Page', ad_html=render('ad1')) }}

When `check_mtimes` is off (the default), calling `render()` is super-fast,
and after the first time when the module is imported, it basically amounts to
a couple of dict lookups.


Customizing Renderer
--------------------

To customize rendering settings, simply pass arguments to the `Renderer()`
initializer as follows:

* **template_dir** is the only required argument -- it specifies the root
directory of your Symplate source files.
* **output_dir** is the directory the compiled Python template files will go
into. The default is `symplouts` at the same level as your `template_dir`.
* **extension** is the file extension for templates. The default is `'.symp'`.
Set this to `''` if you want to specify the file extension explicitly when
calling render.
* **check_mtimes** is off by default. Set to True to tell Symplate to check
the template files' modify times on render, which is slower and usually only
used for debugging.
* **modify_path** is on by default, and means Symplate will put
`output_dir/..` first on `sys.path` so it can import compiled templates. Set
to False if you want to manage this manually.
* **preamble** defaults to empty string, and specifies extra code to include
at the top of all compiled template. Useful for imports you use in many
templates.
* **default_filter** defaults to `'symplate.html_filter'`, and is used to
[override the default filter](#overriding-the-default-filter).

The public methods of `Renderer` instances are `render`, `compile`, and
`compile_all`, though often you'll only need `render`. You use these functions
as follows:

```python
# first create a Renderer
renderer = symplate.Renderer(template_dir)

# render named template with given positional and keyword args and return
# output as a unicode string
output = renderer.render('home', *args, **kwargs)

# compile named template to a .py file in output directory; this will be
# done automatically the first time you call render(), but you can do it
# manually too
renderer.compile('home')

# compile all templates in template_dir to .py files; specify
# "recursive=False" if you don't want it to recurse into sub-directories
renderer.compile_all()
```

Unicode handling
----------------

Symplate templates have full support for Unicode. The template files are
always encoded in UTF-8, and internally Symplate builds the template as
unicode.

`render()` always returns a unicode string, and it's best to pass unicode
strings as arguments to `render()`, but you can also pass UTF-8 byte strings,
as the default filter `html_filter` will handle both.


Command line usage
------------------

`symplate.py` can also be run as a command-line script. This is currently only
useful for pre-compiling one or more templates, which might be useful in a
constrained deployment environment where you can only upload Python code, and
not write to the file system.

Simply specify arguments as per your `Renderer`, and it'll compile all your
templates to Python code. Quoting from the command line help:

    Usage: symplate.py [-h] [options] template_dir [template_names]

    Compile templates in specified template_dir, or all templates if
    template_names not given

    Options:
      --version             show program's version number and exit
      -h, --help            show this help message and exit
      -o OUTPUT_DIR, --output-dir=OUTPUT_DIR
                            compiled template output directory, default
                            {template_dir}/../symplouts
      -e EXTENSION, --extension=EXTENSION
                            file extension for templates, default .symp
      -p PREAMBLE, --preamble=PREAMBLE
                            template preamble (see docs), default ""
      -q, --quiet           don't print what we're doing
      -n, --non-recursive   don't recurse into subdirectories


Meta
----

### Hats off to bottle.py

Literally a few days after I wrote a draft version of Symplate, I saw a
reference to [Bottle](http://bottlepy.org) on Hacker News, and discovered the
author of that had almost exactly the same idea (no doubt some time earlier).
I thought of it independently, honest! Perhaps a good argument against
software patents...

However, after seeing Bottle, one thing I did steal was its use of `!` to
denote raw output. It seemed cleaner (and better for performance reasons) than
my initial idea of passing `raw=True` as a parameter to the filter, as in
`{{ foo, raw=True }}`.

### To-do

Some things I'd like to do or look into when I get a chance:

* Add Python 3 support. Shouldn't be hard, especially if we only care about
  Python 2.6+.
* Can we get original line numbers by outputting `# line: N` comments and then
  reading those when an error occurs?
* Investigate template inheritance, perhaps in the style of bottle.py.

### Flames, comments, bug reports

Please send flames, comments, and questions about Symplate to Ben Hoyt:

http://benhoyt.com/

File bug reports or feature requests at the GitHub project page:

https://github.com/benhoyt/symplate
