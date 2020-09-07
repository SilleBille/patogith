#!/usr/bin/python3

# --- BEGIN COPYRIGHT BLOCK ---
# Copyright (C) 2020 Simon Pichugin <simon.pichugin@gmail.com>
# All rights reserved.
#
# License: GPL (version 3 or any later version).
# See LICENSE for details.
# --- END COPYRIGHT BLOCK ---

#
# A setup.py file
#

from setuptools import setup
from os import path


here = path.abspath(path.dirname(__file__))

version = "0.1"

with open(path.join(here, 'README.md'), 'r') as f:
    long_description = f.read()

setup(
    name='patogith',
    license='GPLv3+',
    version=version,
    description='A simple tool for pagure to github migration',
    long_description=long_description,
    url='https://github.com/droideck/patogith',
    author='Simon Pichugin',
    author_email='simon.pichugin@gmail.com',

    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'Operating System :: POSIX :: Linux',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Topic :: Software Development :: Tool',
        'Topic :: Software Development :: Migration'],

    keywords='pagure github migration',
    packages=['patogith'],
    package_dir={'': 'lib', },

    data_files=[
        ('/usr/sbin/', [
            'cli/patogith',
            ]),
    ],

    install_requires=[
        'pygithub',
        'libpagure',
        'python-bugzilla',
        'argcomplete',
        'argparse-manpage',
        'setuptools',
        ],
)
