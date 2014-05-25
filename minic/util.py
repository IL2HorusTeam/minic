# -*- coding: utf-8 -*-
import os


ugettext = lambda x: x
ugettext_lazy = lambda x: x


if os.name == 'posix':
    def pid_exists(pid):
        """
        Check whether pid exists in the current process table is POSIX-like OS.
        """
        import errno
        if pid < 0:
            return False
        try:
            os.kill(pid, 0)
        except OSError as e:
            return e.errno == errno.EPERM
        else:
            return True
else:
    def pid_exists(pid):
        """
        Check whether pid exists in the current process table in Windows.
        """
        import ctypes
        kernel32 = ctypes.windll.kernel32
        SYNCHRONIZE = 0x100000

        process = kernel32.OpenProcess(SYNCHRONIZE, 0, pid)
        exists = process != 0
        if exists:
            kernel32.CloseHandle(process)
        return exists
