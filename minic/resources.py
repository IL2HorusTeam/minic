# -*- coding: utf-8 -*-
import os
import minic


def resource_path(*args):
    return os.path.join(minic.APP_ROOT, 'resources', *args)


def image_path(*args):
    return resource_path('images', *args)
