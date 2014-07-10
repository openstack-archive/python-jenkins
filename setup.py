#!/usr/bin/env python

from distutils.core import setup

with open('requirements.txt') as f:
    required = f.read().splitlines()

setup(name='python-jenkins',
      version='0.3.3',
      description='Python bindings for the remote Jenkins API',
      author='Ken Conley',
      author_email='kwc@willowgarage.com',
      url='http://launchpad.net/python-jenkins',
      packages=['jenkins'],
      install_requires=required,
      )
