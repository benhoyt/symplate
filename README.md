Symplate, the Simple pYthon teMPLATE renderer
=============================================

Symplate is one of the simplest and fastest Python templating languages.


Background
----------

[*Skip the background, show me an example!*](#basic-usage)

When I got frustrated with the complexities and slow rendering speed of
[Cheetah](http://www.cheetahtemplate.org/), I started wondering just how
simple a templating language could be.

It's somewhat painful to write templates in pure Python -- code and text are
hard to intersperse, and you don't get auto-escaping. But why not a KISS
template-to-Python translator? Enter Symplate:

* `text` becomes `_write('text')`
* `{{ expr }}` becomes `_write(filt(expr))`
* `{% code %}` becomes `code` at the correct indentation level
* indentation increases when a code line ends with a colon, as in
  `{% for x in lst: %}`
* indentation decreases when you say `{% end %}`

That's about all there is to it. All the rest is detail.


Who uses Symplate?
------------------

Only me ... so far. It's my experiment. But there's no reason you can't: it's
a proper library, and fairly well tested. I "ported" my
[GiftyWeddings.com](http://giftyweddings.com/) website from Cheetah to
Symplate, and it's working very well.


Why use Symplate?
-----------------

Well, if you care about **raw performance** or **simplicity of
implementation**, Symplate might be for you. I care about both, and I haven't
needed some of the extra features other systems provide, such as sandboxed
execution. If you want a Porshe, use Symplate. If you'd prefer a Volvo or BMW,
I'd recommend [Jinja2](http://jinja.pocoo.org/docs/) or
[Mako](http://www.makotemplates.org/).

Symplate is dead simple: a couple of pages of code translate your templates to
Python `.py` files, and `render()` imports and executes those.

Symplate's also about as fast as a pure-Python templating language can be.
Partly *because* it's simple, it produces Python code as tight as you'd write
it by hand.


Isn't worrying about performance silly?
---------------------------------------

Yes, [worrying about the performance of your template engine is
silly](http://www.codeirony.com/?p=9). Well, sometimes. But when you're doing
zero database requests and your "business logic" is pretty tight, template
rendering is all that's left. And Cheetah (not to mention Django!) are
particlarly slow.

If you're running a large-scale website and you're caching things so that
template rendering *is* your bottleneck ... then if you can take your
rendering time down from 100ms to 20ms, you can run your website on 1/5th the
number of servers.

So how fast is Symplate? About as fast as you can hand-code Python. Here's the
Symplate benchmark showing compile and render times for some of the fast or
popular template languages.

Times are normalized to the HandCoded render time (TODO):

    Engine    compile (ms)  render (ms)
    -----------------------------------
    HandCoded        0.000        0.107
    Symplate         1.385        0.120
    Wheezy           3.214        0.145
    Bottle           1.093        0.277
    Mako             6.567        0.415
    Jinja2           7.149        0.590
    Cheetah         13.299        0.644
    Django           0.839        2.451


Basic usage
-----------

Let's start with a simple example that uses more or less all the features of
Symplate. Our main template is `blog.symp`:

    {% template entries, title='My Blog' %}
    {{ !render('inc/header', title) }}
    <h1>This is {{ title }}</h1>
    {% for entry in entries: %}
        <h2><a href="{{ entry.url }}">{{ entry.title.title() }}</a></h2>
        {{ !entry.html_body }}
    {% end for %}
    </ul>
    {{ !render('inc/footer') }}

In Python fashion, everything's explicit. We explicitly specify the parameters
this template takes in the `{% template ... %}` line, including the default
parameter `title`.

For simplicity, there's no special "include" directive -- you just `render()`
a sub-template -- usually with the `!` prefix to mean don't filter the
rendered output. The arguments passed to `render()`ed sub-templates are
specified explicitly, so there's no yucky setting of globals when rendering
included templates. (Note: `render` is set to the current Renderer instance's
`render` function.)

In this example, `entry.html_body` contains pre-rendered HTML, so this
expression is also prefixed with `!` -- it will output the HTML body as a raw,
unescaped string.

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

    renderer = symplate.Renderer(template_dir)
    output = renderer.render('blog', entries, title="Ben's Blog")

You can customize the Renderer to specify a different output directory, or to
turn on checking of template file mtimes for debugging. For example:

    renderer = symplate.Renderer(template_dir, output_dir='out',
                                 check_mtime=DEBUG)

    def homepage():
        entries = load_blog_entries()
        return renderer.render('blog', entries, title="Ben's Blog")

See `Renderer.__init__`'s docstring or type `help(symplate.Renderer)` at a
Python prompt for docs on the exact arguments for `Renderer()`.


Compiled Python output
----------------------

Symplate is a [leaky abstraction](http://www.joelonsoftware.com/articles/LeakyAbstractions.html),
but is somewhat proud of that fact. I already knew Python well, so my goal was
to be as close to Python as possible -- I don't want to learn another language
just to produce some HTML.

In any case, you're encouraged to look at the compiled Python output produced
by the Symplate compiler. You might be surprised how clean it looks. Symplate
tries to make the compiled template look much like it would if you were
writing it by hand -- for example, short strings are output as `'shortstr'`,
and long, multi-line strings as `"""long, multi-line strings"""`.

The `blog.symp` example above produces this in `blog.py`:

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

As you can see, apart from a tiny premable, it's about as fast and direct as
it could possibly be (in pure Python).

Basic Symplate syntax errors like mismatched `{%`'s are raised as
`symplate.Error`s when the template is compiled. However, most Python
expressions are copied directly to the Python output, so you only get a Python
SyntaxError when the compiled template is imported at render time. (Yes, this
is a minor drawback of Symplate's KISS approach.)


Directives
----------

The only directives or keywords in Symplate are `template` and `end`. Oh, and
"colon at the end of a code line".

`{% template [args] %}` must appear at the start of a template before any
output. `args` is the argument specification including positional and
keyword/default arguments, just as if it were a function definition. In fact,
it is -- `{% template [args] %}` gets compiled to
`def render(_renderer, args): ...`.

If you need to import other modules, do so at the top of your template, above
the `template` directive (just like in Python you import before writing code).

`{% end [...] %}` ends a code indentation block. All it does is reduce the
indentation level in the compiled Python output. The `...` is optional, and
acts as a comment, so you can say `{% end for %}` or `{% end if %}` if you
like.

A `:` (colon) at the end of a code block starts a code indentation block, just
like in Python. However, there's a special case for the `elif`, `else`,
`except` and `finally` keywords -- they dedent for the line the keyword is on,
and then indent again (just like you would when writing Python).


Filters
-------

### The default filter

The default filter used by `{{ ... }}` output expressions is `html_filter`,
which escapes HTML/XML special characters in the given string. It escapes `&`,
`<`, `>`, `'`, and `"`, so it's good for both HTML content as well as
attribute values.

For example, `render('test', thing='A & B', title="Symplate's simple")` on
this template:

    Thing is <b>{{ thing }}</b>.
    <img src='logo.png' title='{{ title }}'>

Would produce the output:

    Thing is <b>A &amp; B</b>.
    <img src='logo.png' title='Symplate&#39;s simple'>

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

### Changing the default filter

You can change the default filter by passing `Renderer` the `default_filter`
argument. If this is a string, it's used directly for setting the filter, as
per the above:

    # this default filter will make everything uppercase
    renderer = symplate.Renderer(default_filter='lambda s: s.upper()')

If it's not a string, it must be a function which takes a single `filename`
(the template filename) as its argument. This is useful when, for example, you
want to determine the default filter based on the template's file extension.
A simple example:

    # this default filter will use json.dumps() for .js.symp files and the
    # normal HTML filter for other files
    def get_default_filter(self, filename):
        if filename.lower().endswith('.js.symp'):
            return 'json.dumps'
        else:
            return 'symplate.html_filter'
    renderer = symplate.Renderer(default_filter=get_default_filter,
                                 preamble='import json\n')

Note the modified `premable` so the compiled template has the `json` module
available.


Unicode handling
----------------

Symplate templates have full support for Unicode. The template files are
always encoded in UTF-8, and internally Symplate builds the template as
unicode.

`render()` always returns a unicode string, and it's best to pass unicode
strings as arguments to `render()`, but you can also pass ASCII byte strings,
as the default filter `html_filter` will handle both.


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

    TODO


Hats off to bottle.py
---------------------

Literally a few days after I wrote a draft version of Symplate, I saw a
reference to [Bottle](http://bottlepy.org) on Hacker News, and discovered the
author of that had almost exactly the same idea (no doubt some time earlier).
I thought of it independently, honest! Perhaps a good argument against
software patents...

However, after seeing Bottle, one thing I did steal was its use of `!` to
denote raw output. It seemed cleaner than my initial idea of passing
`raw=True` as a parameter to the filter, as in `{{ foo, raw=True }}`.


Flames, comments, bug reports
-----------------------------

Please send flames, comments, and questions about Symplate to Ben Hoyt:

http://benhoyt.com/

File bug reports or feature requests at the GitHub project page:

https://github.com/benhoyt/symplate
