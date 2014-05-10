# -*- coding: utf-8 -*-
import gtk
import py2exe
import os

from setuptools import setup, find_packages


GTK_RUNTIME_DIR = os.path.join(
    os.path.split(os.path.dirname(gtk.__file__))[0], "runtime")

assert os.path.exists(GTK_RUNTIME_DIR), "Cannot find GTK runtime data"


setup(
    name='minic',
    version='1.0.0',
    description='Minicommander for IL-2 FB Dedicated Server',
    license='GPLv2',
    url='https://github.com/IL2HorusTeam/minic',
    author='Alexander Oblovatniy',
    author_email='oblovatniy@gmail.com',
    scripts=[
        'application.py',
    ],
    packages=find_packages(),
    install_requires=[i.strip() for i in open("requirements.pip").readlines()],
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: End Users/Desktop',
        'License :: Free for non-commercial use',
        'Natural Language :: English',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 2.7',
        'Topic :: Communications',
        'Topic :: Games/Entertainment :: Simulation',
        'Topic :: System :: Systems Administration',
        'Topic :: Utilities',
    ],
    windows=[
        {
            'script': 'application.py',
        }
    ],
)
