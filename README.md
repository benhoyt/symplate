Symplate, the Simple pYthon teMPLATE renderer
=============================================

Usage
-----

* TODO


Filters
-------

* TODO: discuss filt (not called filter due to builtin) and get_default_filter


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
