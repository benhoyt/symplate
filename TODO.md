* if simple, use _output.extend when writing multiple strings
* add Django benchmark per Mako:
  - http://www.makotemplates.org/trac/browser/examples/bench/basic.py
  - https://docs.djangoproject.com/en/dev/ref/templates/api/#configuring-the-template-system-in-standalone-mode
* improve error handling line numbers and text
* simplify os.walk/relpath stuff in _main?
  - perhaps add a compile_all to Renderer instead
* can we get original line numbers by outputting "# line: N" comments and then reading them?
* add setup.py and make into proper package
* investigate inheritance in style of bottle.py?
* Python 3 support?
