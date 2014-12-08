# -*- coding: utf-8 -*-

import os
import subprocess
from setuptools import setup, find_packages, Command
from jekyll2nikola import __version__


def read_description():
    with open('README.rst') as fd:
        return fd.read()


class PyTest(Command):
    user_options = []
    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        import sys,subprocess
        if not os.path.exists('runtests.py'):
            subprocess.call(['py.test', '--genscript=runtests.py'])
        errno = subprocess.call([
            sys.executable, 'runtests.py',
            '--cov', 'jekyll2nikola',
            'tests',
            '--cov-report=term-missing',
        ])
        raise SystemExit(errno)


setup(name='jekyll2nikola',
      version=','.join(str(x) for x in __version__),
      description="",
      long_description=read_description(),
      cmdclass = {'test': PyTest},
      classifiers=[
          'Development Status :: 2 - Pre-Alpha',
          'Programming Language :: Python :: 2.6',
          'Programming Language :: Python :: 2.7',
          'Programming Language :: Python :: 3.2',
          'Programming Language :: Python :: 3.3',
          'Programming Language :: Python :: 3.4',
          'Environment :: Console',
          'Intended Audience :: Developers',
          'License :: OSI Approved :: MIT License',
          'Operating System :: OS Independent',
      ],
      keywords='jekyll octopress nikola',
      author='Miguel Ángel García',
      author_email='miguelangel.garcia@gmail.com',
      url='https://github.com/magmax/jekyll2nikola',
      license='MIT',
      packages=find_packages(exclude=['tests']),
      include_package_data=True,
      zip_safe=False,
      install_requires=[
          'pyyaml',
          'python-dateutil',
      ],
      )
