#!/usr/bin/env python3
# -*- coding: utf-8, vim: expandtab:ts=4 -*-

import setuptools
from webarticlecurator import __version__

with open('README.md') as fh:
    long_description = fh.read()

setuptools.setup(
    name='webarticlecurator',
    version=__version__,
    author='dlazesz',  # Will warn about missing e-mail
    description='A crawler program to download content from portals (news, forums, blogs) and convert it'
                ' to the desired output format according to the configuration.',
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='https://github.com/ELTE-DH/WebArticleCurator',
    # license='GNU Lesser General Public License v3 (LGPLv3)',  # Never really used in favour of classifiers
    # platforms='any',  # Never really used in favour of classifiers
    packages=setuptools.find_packages(exclude=['tests']),
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: GNU Lesser General Public License v3 (LGPLv3)',
        'Operating System :: POSIX :: Linux',
    ],
    python_requires='>=3.7',
    install_requires=['pyyaml', 'chardet', 'requests', 'urllib3', 'warcio', 'ratelimit', 'beautifulsoup4', 'yamale',
                      'newspaper3k'],  # Newspaper3k is optional!
    # pip install webarticlecurator[newspaper3k]
    extras_require={'newspaper3k': ['newspaper3k>=0.2.8,<1.0.0']},
    include_package_data=True,
    entry_points={
        'console_scripts': [
            'webarticlecurator=webarticlecurator.__main__:main',
        ]
    },
)
