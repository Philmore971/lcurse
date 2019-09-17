#!/usr/bin/env python3

from distutils.core import setup

setup(
        name='Lcurse-FR',
        version='2.1.0',
        description='Client Curse compatible pour Linux.',
        url='https://github.com/Philmore971/lcurse',
        packages=['modules'],
        scripts=['lcurse', 'console.py'],
        license='Unlicense',
)
