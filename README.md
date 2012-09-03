Symplate, the Simple pYthon teMPLATE renderer
=============================================

Usage
-----

* TODO


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

Note that the `{% include ... %}` directive:

    {% include 'template.symp', arg1=value1, arg2=value2 %}

is just a less crufty way of spelling:

    {{ !symplate.render('template.symp', arg1=value1, arg2=value2) }}

### Setting the filter

TODO: should filt be something else to avoid potential local naming conflicts?

To set the current filter, just say `{% filt = filter_function %}`. `filt` is
simply a local variable in the compiled template, so don't use is for other
things. `filt` should be a function which takes a single argument and returns
a unicode string.

The expression inside a `{{ ... }}` is passed directly to the current `filt`
function, so you can pass other arguments to custom filters. For example:

    {% filt = json.dumps %}
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


Outputting a literal {{
-----------------------

You can't include {{ or }} anywhere inside an output expression, and you can't
include {% or %} anywhere inside a code block. To output a literal {{, }}, {%,
or %}, use Python's string literal concatenation so the two {'s are separated.
For example, this will output a single {{:

    {{ '{' '{' }}

If you find yourself needing this a lot (for instance in writing a template
about templates), you could shortcut and name it at the top of your template:

    {% LB, RB = '{' '{', '}' '}' %}
    {{LB}}one{{RB}}
    {{LB}}two{{RB}}
    {{LB}}three{{RB}}


Default Renderer and customizing
--------------------------------

* TODO


Command line usage
------------------

Symplate (symplate.py) can also be run as a command-line script. This is
currently only useful for pre-compiling one or more templates, which might be
useful in a constrained deployment environment where you can only upload
Python code, and not write to the file system.

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
