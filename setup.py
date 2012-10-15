"""Run "python setup.py install" to install Symplate."""

from distutils.core import setup

import symplate

setup(
    name='Symplate',
    version=symplate.__version__,
    author='Ben Hoyt',
    author_email='benhoyt@gmail.com',
    url='https://github.com/benhoyt/symplate',
    license='New BSD License',
    description='Symplate, the Simple pYthon teMPLATE renderer',
    long_description='Symplate is a very simple and very fast Python template language. Read more at the GitHub project page.',
    py_modules=['symplate'],
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'Operating System :: OS Independent',
        'License :: OSI Approved :: BSD License',
        'Programming Language :: Python',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
    ]
)
