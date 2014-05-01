#!/usr/bin/env python
# -*- coding: utf-8 -*-
import pygtk
pygtk.require('2.0')

from twisted.internet import gtk2reactor
gtk2reactor.install()

import gtk

from twisted.internet import reactor
from minic.ui import MainWindow


if __name__ == "__main__":
    #log.startLogging(sys.stdout)
    gtk.settings_get_default().props.gtk_button_images = True
    MainWindow()
    reactor.run()
