"""Run "python setup.py install" to install Symplate."""

from distutils.core import setup

import symplate

setup(
    name='Symplate',
    version=symplate.__version__,
    author='Ben Hoyt',
    author_email='benhoyt@gmail.com',
    url='https://github.com/benhoyt/symplate',
    license='LICENSE.txt',
    description='A very simple and very fast Python template language',
    long_description=open('README.md').read(),
    py_modules=['symplate'],
)
