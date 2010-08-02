#!/usr/bin/env python

from distutils.core import setup

setup(name='Quickdesktop',
      version='1.0',
      description='High level UI building libraries',
      author='Vikrant Patil',
      author_email='vikrant.patil@gmail.com',
      url='http://vikipedia.github.com/quickdesktop',
      packages=['quickdesktop'], 
      package_dir = {'quickdesktop':"src/quickdesktop"},
      data_files = [('',['releasenotes.txt'])],
      requires = ['pygtk (>2.0)'],
      license = 'LGPL',
      platforms = ['linux','windows']
     )