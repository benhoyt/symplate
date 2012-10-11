"""Script to render Symplate whitespace example."""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
import symplate

renderer = symplate.Renderer(
        os.path.join(os.path.dirname(__file__), 'symplates'),
        output_dir=os.path.join(os.path.dirname(__file__), 'symplouts'),
        check_mtimes=True)

def main():
    output = renderer.render('whitespace')
    sys.stdout.write(output.encode('utf-8'))

if __name__ == '__main__':
    main()
