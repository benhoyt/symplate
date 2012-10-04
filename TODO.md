* ensure there's a simple way to get it to recompile all templates once on startup (or the first time they're used)
  - perhaps just a force=False param to _get_module()
* are there tests for check_mtime stuff? and the above?
* can we get original line numbers by outputting "# line: N" comments and then reading them?
* add setup.py and make into proper package
  - http://docs.python.org/distutils/index.html
  - http://guide.python-distribute.org/index.html
  - add LICENSE.txt, CHANGES.txt
* investigate inheritance in style of bottle.py?
* Python 3 support?
