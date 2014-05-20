# -*- coding: utf-8 -*-
import unittest

import minic


class CommonsTestCase(unittest.TestCase):

    def test_version_lt(self):
        self.assertTrue(minic.version_lt((0, 0, 0), (0, 0, 1)))
        self.assertTrue(minic.version_lt((0, 0, 0), (0, 1, 0)))
        self.assertTrue(minic.version_lt((0, 0, 0), (0, 1, 1)))
        self.assertTrue(minic.version_lt((0, 0, 0), (1, 0, 0)))
        self.assertTrue(minic.version_lt((0, 0, 0), (1, 0, 1)))
        self.assertTrue(minic.version_lt((0, 0, 0), (1, 1, 0)))
        self.assertTrue(minic.version_lt((0, 0, 0), (1, 1, 1)))

        self.assertFalse(minic.version_lt((0, 0, 1), (0, 0, 1)))
        self.assertFalse(minic.version_lt((0, 1, 0), (0, 0, 1)))
        self.assertFalse(minic.version_lt((0, 1, 1), (0, 0, 1)))
        self.assertFalse(minic.version_lt((1, 0, 0), (0, 0, 1)))
        self.assertFalse(minic.version_lt((1, 0, 1), (0, 0, 1)))
        self.assertFalse(minic.version_lt((1, 1, 0), (0, 0, 1)))
        self.assertFalse(minic.version_lt((1, 1, 1), (0, 0, 1)))

        self.assertTrue(minic.version_lt((0, 1, 0), (0, 1, 1)))
        self.assertTrue(minic.version_lt((0, 1, 0), (1, 0, 0)))
        self.assertTrue(minic.version_lt((0, 1, 0), (1, 0, 1)))
        self.assertTrue(minic.version_lt((0, 1, 0), (1, 1, 0)))
        self.assertTrue(minic.version_lt((0, 1, 0), (1, 1, 1)))

        self.assertFalse(minic.version_lt((0, 1, 0), (0, 1, 0)))
        self.assertFalse(minic.version_lt((0, 1, 1), (0, 1, 0)))
        self.assertFalse(minic.version_lt((1, 0, 0), (0, 1, 0)))
        self.assertFalse(minic.version_lt((1, 0, 1), (0, 1, 0)))
        self.assertFalse(minic.version_lt((1, 1, 0), (0, 1, 0)))
        self.assertFalse(minic.version_lt((1, 1, 1), (0, 1, 0)))

        self.assertTrue(minic.version_lt((1, 0, 0), (1, 0, 1)))
        self.assertTrue(minic.version_lt((1, 0, 0), (1, 1, 0)))
        self.assertTrue(minic.version_lt((1, 0, 0), (1, 1, 1)))

        self.assertFalse(minic.version_lt((1, 0, 1), (1, 0, 0)))
        self.assertFalse(minic.version_lt((1, 1, 0), (1, 0, 0)))
        self.assertFalse(minic.version_lt((1, 1, 1), (1, 0, 0)))
