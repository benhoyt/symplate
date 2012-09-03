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

* TODO


Comments
--------

* TODO: {% # foo %}, and note that you can't do {% for x in y: # comment %}


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

* TODO
