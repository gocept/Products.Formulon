# -*- coding: utf-8 -*-
# Copyright (c) 2010 gocept gmbh & co. kg
# See also LICENSE.txt

import os.path
import setuptools


def read(*path_elements):
    return "\n\n" + file(os.path.join(*path_elements)).read()


version = '1.0.4dev'

setuptools.setup(
    name='Products.Formulon',
    version=version,
    description="Form objects for Zope 2",
    long_description=(
        '.. contents::' +
        read('README.txt') +
        read('TODO.txt') +
        read('CHANGES.txt')
        ),
    keywords='form',
    author='gocept gmbh & co. kg',
    author_email='mh@gocept.com',
    url='http://code.gocept.com',
    license='GPL2',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Programming Language :: Python',
        ],
    packages=setuptools.find_packages('src'),
    package_dir = {'': 'src'},
    namespace_packages = ['Products'],
    include_package_data=True,
    zip_safe=False,
    install_requires=[
        'setuptools',
        'zope.cachedescriptors',
        ],
    extras_require = dict(
        test=[
            'zope.testing',
            ],
        ),
    )
