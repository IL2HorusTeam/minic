# -*- coding: utf-8 -*-
import os


RESOURCES_PATH = os.path.dirname(os.path.abspath(__file__))


def resource_path(*args):
    return os.path.join(RESOURCES_PATH, *args)


def image_path(*args):
    return resource_path('images', *args)


def ui_path(name):
    name = name + '.glade'
    return resource_path('ui', name)
