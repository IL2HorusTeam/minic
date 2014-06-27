minic
=====

Minicommander for IL-2 FB DS.

.. image:: http://i.imgur.com/IceQg1U.png
    :alt: Minic screenshots
    :align: center

Releases
--------

0.1.12
^^^^^^

:Date: 27.06.2014
:Download links:
    `Windows <https://drive.google.com/file/d/0B4hbTGD5PQqQMTdsa1BPd3BTaGc/edit?usp=sharing>`_,
    `Linux/Mac <https://github.com/IL2HorusTeam/minic/archive/0.1.12.zip>`_
:Changes:
    `Issues <https://github.com/IL2HorusTeam/minic/issues?milestone=1&state=closed>`_,
    `code changes <https://github.com/IL2HorusTeam/minic/compare/0.1.0...0.1.12>`_

Hot fixes for the 1st release. Key points:

* Ensure relative paths to missions files have no leading slashes (`#1`_);
* Ensure editing of mission list does not affect running mission (`#2`_);
* Activate menu items with single click instead of double click (`#4`_);
* Ensure ``localHost`` parameter is set in server's config (`#7`_);
* Ensure only one instance of application can be created (`#8`_);
* Update ``il2ds-middleware`` dependency up to version ``0.10.3`` to handle
  connection exceptions on russified Windows (`#9`_);
* Add version number to user settings (`#11`_);
* Fix chat messages about mission state when current mission is changed
  manually while mission was playing (`#12`_);
* Disable ``Next`` and ``Previous`` buttons if there is only one mission in
  missions list (`#14`_);
* Ensure mission's duration is positive integer above zero (`#15`_);
* Hide log dialog produced by ``py2exe`` when a new log file is created due to
  unhandled exceptions (`#17`_).

0.1.0
^^^^^

:Date: 10.05.2014
:Download links:
    `Windows <https://drive.google.com/file/d/0B4hbTGD5PQqQYVJ6dWJ6NEVJQmM/edit?usp=sharing>`_,
    `Linux/Mac <https://github.com/IL2HorusTeam/minic/archive/0.1.0.zip>`_

Initial version. Includes:

* Connecting to IL-2 FB server with reconnection support.
* Missions list definition and managing. Each mission has it's own:

  - order number;
  - verbose name;
  - path to file;
  - duration in minutes;

* Game flow control:

  - go to first;
  - go to previous;
  - stop current;
  - start;
  - restart current;
  - go to next;
  - go to last.

Licence
-------

`GNU General Public License v2 (GPLv2)`_, free for non-commercial use.

For developers
--------------

Please see `DEVELOPMENT`_.

.. _GNU General Public License v2 (GPLv2): https://github.com/IL2HorusTeam/minic/blob/master/LICENSE
.. _DEVELOPMENT: https://github.com/IL2HorusTeam/minic/blob/master/DEVELOPMENT.rst

.. _#1: https://github.com/IL2HorusTeam/minic/issues/1
.. _#2: https://github.com/IL2HorusTeam/minic/issues/2
.. _#4: https://github.com/IL2HorusTeam/minic/issues/4
.. _#7: https://github.com/IL2HorusTeam/minic/issues/7
.. _#8: https://github.com/IL2HorusTeam/minic/issues/8
.. _#9: https://github.com/IL2HorusTeam/minic/issues/9
.. _#11: https://github.com/IL2HorusTeam/minic/issues/11
.. _#12: https://github.com/IL2HorusTeam/minic/issues/12
.. _#14: https://github.com/IL2HorusTeam/minic/issues/14
.. _#15: https://github.com/IL2HorusTeam/minic/issues/15
.. _#17: https://github.com/IL2HorusTeam/minic/issues/17
