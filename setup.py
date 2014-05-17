# -*- coding: utf-8 -*-
import gtk
import py2exe
import os

from distutils.core import setup


GTK_RUNTIME_DIR = os.path.join(
    os.path.split(os.path.dirname(gtk.__file__))[0], "runtime")

assert os.path.exists(GTK_RUNTIME_DIR), "Cannot find GTK runtime data"

GTK_THEME_DEFAULT = os.path.join("share", "themes", "Default")
GTK_THEME_WINDOWS = os.path.join("share", "themes", "MS-Windows")

GTK_ENGINE_DIR = os.path.join("lib", "gtk-2.0", "2.10.0", "engines")
GTK_ENGINE_DLL = "libwimp.dll"

GTK_LOCALE_DATA = os.path.join("share", "locale")
GTK_EXTRA_LOCALES = ['ru', ]

GTK_ICONS = os.path.join("share", "icons")

APP_IMAGES_PATH = os.path.join('resources', 'images')


def alias_subdir(root, subdir):
    suffix_length = len(root) + 1
    full_location = os.path.join(root, subdir)
    result = []
    for dirname, subdirs, filenames in os.walk(full_location):
        if filenames:
            result.append((
                dirname[suffix_length:],
                [os.path.join(dirname, filename) for filename in filenames],
            ))
    return result


data_files = [
    (APP_IMAGES_PATH, [
        os.path.join(APP_IMAGES_PATH, 'logo.png'),
        os.path.join(APP_IMAGES_PATH, 'show.png'),
        os.path.join(APP_IMAGES_PATH, 'hide.png'),
    ]),
    (GTK_ENGINE_DIR, [
        os.path.join(GTK_RUNTIME_DIR, GTK_ENGINE_DIR, GTK_ENGINE_DLL),
    ]),
]
data_files.extend(alias_subdir(GTK_RUNTIME_DIR, GTK_THEME_DEFAULT))
data_files.extend(alias_subdir(GTK_RUNTIME_DIR, GTK_THEME_WINDOWS))

version = __import__('minic').get_version()

setup(
    name='minic',
    version=version,
    description='Minicommander for IL-2 FB Dedicated Server',
    license='GPLv2',
    url='https://github.com/IL2HorusTeam/minic',
    author='Alexander Oblovatniy',
    author_email='oblovatniy@gmail.com',
    scripts=[
        'application.py',
    ],
    packages=[
        'minic', 'minic.service',
    ],
    windows=[
        {
            'script': 'application.py',
            'icon_resources': [(1, os.path.join(APP_IMAGES_PATH, 'logo.ico'))],
        },
    ],
    data_files=data_files,
    options={
        'py2exe': {
            'packages': [
                'encodings', 'candv', 'il2ds_middleware', 'twisted', 'tx_logging',
            ],
            'includes': [
                'cairo', 'pango', 'pangocairo', 'gobject', 'gio', 'atk',
            ],
            'excludes': [
                '_gtkagg', '_tkagg', 'bsddb', 'curses', 'pywin.debugger',
                'pywin.debugger.dbgcon', 'email', 'calendar', 'unittest',
                'urllib', 'urllib2', 'xml', 'tcl', 'Tkconstants', 'Tkinter',
                'gtk.glade',
            ],
            'optimize': 2,
        }
    },
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: End Users/Desktop',
        'License :: Free for non-commercial use',
        'License :: OSI Approved :: GNU General Public License v2 (GPLv2)',
        'Natural Language :: English',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 2.7',
        'Topic :: Communications',
        'Topic :: Games/Entertainment :: Simulation',
        'Topic :: System :: Systems Administration',
        'Topic :: Utilities',
    ],
)
