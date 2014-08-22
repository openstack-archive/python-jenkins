#!/usr/bin/env python

from distutils.core import setup

setup(name='python-jenkins',
      version='0.3.4',
      description='Python bindings for the remote Jenkins API',
      author='Ken Conley',
      author_email='kwc@willowgarage.com',
      url='http://launchpad.net/python-jenkins',
      packages=['jenkins'],
      install_requires=['six'],
      )
