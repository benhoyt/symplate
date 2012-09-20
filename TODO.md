* investigate whitespace in output (also for performance), especially between two {%...%} directives
* consider removing non-string handling from html_filter to simplify/speed up (caller can do this)
* improve error handling line numbers and text
* look at http://wiki.python.org/moin/Templating, particularly wheezy.template for speed
* simplify os.walk/relpath stuff in _main?
  - perhaps add a compile_all to Renderer instead
* can we get original line numbers by outputting "# line: N" comments and then reading them?
* add setup.py and make into proper package
* investigate inheritance in style of bottle.py?
* Python 3 support?
