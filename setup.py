'''
How to upload

python setup.py clean sdist bdist_wheel
twine upload dist/*
'''


# Always prefer setuptools over distutils
from setuptools import setup, find_packages
# To use a consistent encoding
from codecs import open
from os import path
from mdvl import __version__, __author__

here = path.abspath(path.dirname(__file__))

# Get the long description from the README file
with open(path.join(here, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

setup(
    name='mdvl',

    version=__version__,

    description='Lightweight Terminal Markdown Renderer',
    long_description=long_description,

    url='https://github.com/axiros/mdvl',

    author=__author__,
    author_email='gk@axiros.com',

    license='BSD',

    # See https://pypi.python.org/pypi?%3Aaction=list_classifiers
    classifiers=[
        # How mature is this project? Common values are
        #   3 - Alpha
        #   4 - Beta
        #   5 - Production/Stable
        'Development Status :: 4 - Beta',

        'Intended Audience :: Developers',
        "Topic :: Text Processing :: Markup",
        "Operating System :: POSIX",

        'License :: OSI Approved :: BSD License',

        # Specify the Python versions you support here. In particular, ensure
        # that you indicate whether you support Python 2, Python 3 or both.
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
    ],

    keywords=['markdown', 'markup', 'terminal', 'hilighting', 'syntax', 'source code'],

    py_modules=['mdvl'],
    zip_safe=False,
    entry_points={
        'console_scripts': [ 'mdvl=mdvl:sys_main' ],
    },
)
