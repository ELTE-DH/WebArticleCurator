#!/usr/bin/env pyhton3
# -*- coding: utf-8, vim: expandtab:ts=4 -*-

import setuptools
from corpusbuilder import __version__

with open('README.md') as fh:
    long_description = fh.read()

setuptools.setup(
    name='corpusbuilder',
    version=__version__,
    author='dlazesz',  # Will warn about missing e-mail
    description='Corpus generator program to download content of Hungarian online newspapers',
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='https://github.com/dlazesz/corpusbuilder',
    # license='GNU Lesser General Public License v3 (LGPLv3)',  # Never really used in favour of classifiers
    # platforms='any',  # Never really used in favour of classifiers
    packages=setuptools.find_packages(exclude=['tests']),
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: GNU Lesser General Public License v3 (LGPLv3)',
        'Operating System :: POSIX :: Linux',
    ],
    python_requires='>=3.6',
    install_requires=['pyyaml', 'chardet', 'requests', 'urllib3', 'warcio', 'ratelimit', 'beautifulsoup4',
                      'newspaper3k'],  # Newspaper3k is optional!
    include_package_data=True,
    entry_points={
        'console_scripts': [
            'corpusbuilder=corpusbuilder.__main__:main',
        ]
    },
)
