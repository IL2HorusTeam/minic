# -*- coding: utf-8 -*-
import os
import tx_logging

from collections import namedtuple

from minic.settings import user_settings
from minic.util import ugettext_lazy as _


LOG = tx_logging.getLogger(__name__)

Mission = namedtuple('Mission',
                     field_names=['id', 'name', 'relative_path', 'duration'])


class MissionManager(object):

    _id_generator = None
    _first_load_flag = True
    dogfight_subpath = os.path.join('Net', 'dogfight')

    @classmethod
    def _get_raw(cls):
        value = user_settings.missions
        if value is None:
            value = {
                'list': [],
                'current_id': None,
            }
            user_settings.missions = value
        return value

    @classmethod
    def all(cls):
        missions = cls._get_raw().setdefault('list', [])
        if cls._first_load_flag:
            return list(map(lambda x: Mission(*x), missions))
            cls._first_load_flag = False
        else:
            return missions

    @classmethod
    def update(cls, missions):
        cls._get_raw()['list'] = [Mission(*x) for x in missions]
        user_settings.sync()

    @classmethod
    def count(cls):
        return len(cls.all())

    @classmethod
    def get_current_id(cls):
        return cls._get_raw().setdefault('current_id', None)

    @classmethod
    def set_current_id(cls, value):
        cls._get_raw()['current_id'] = value
        user_settings.sync()

    @classmethod
    def generate_id(cls):
        if cls._id_generator is None:

            def id_generator():
                number = max([m.id for m in cls.all()] or [0, ])
                while True:
                    number += 1
                    yield number

            cls._id_generator = id_generator()
        return next(cls._id_generator)

    @classmethod
    def get_current_mission(cls):
        current_id = cls.get_current_id()
        if current_id is not None:
            for m in cls.all():
                if m.id == current_id:
                    return m

    @classmethod
    def get_index_by_id(cls, mission_id):
        index = -1
        for i, m in enumerate(cls.all()):
            if m.id == mission_id:
                index = i
                break
        return index

    @classmethod
    def get_id_by_index(cls, index):
        try:
            return cls.all()[index].id
        except ValueError:
            return None

    @classmethod
    def get_root_path(cls):
        return os.path.join(
            os.path.dirname(user_settings.server_path),
            'Missions',
            cls.dogfight_subpath)

    @classmethod
    def absolute_path(cls, short_relative_path):
        return os.path.join(cls.get_root_path(), short_relative_path)

    @classmethod
    def short_relative_path(cls, absolute_path):
        root_path = cls.get_root_path()
        if absolute_path.startswith(root_path):
            return absolute_path[len(root_path) + len(os.path.sep):]
        raise ValueError(_("Missions must be placed within '{0}' directory.")
                         .format(root_path))

    @classmethod
    def full_relative_path(cls, short_relative_path):
        return os.path.join(cls.dogfight_subpath, short_relative_path)
