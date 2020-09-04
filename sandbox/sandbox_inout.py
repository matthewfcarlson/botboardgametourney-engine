##############################################################################
#
# Copyright (c) 2002 Zope Foundation and Contributors.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE
#
##############################################################################
from __future__ import print_function
import asyncio
from io import BufferedRandom
from io import BytesIO

class SandboxInOut(object):
    """Collect written text, and return it when called."""

    class InnerSandboxInOut(object):
        def __init__(self, printer, _getattr_=None):
            self.printer = printer
            self._getattr_ = _getattr_
        def write(self, text:str):
            self.printer.write(text, consumer=False)
        def read(self):
            line = self.printer.readline(consumer=True)
            if len(line) == 0:
                return None
            return str(line)
        def __call__(self, testing = None):
            return self
        def _call_print(self, *objects, **kwargs):
            if kwargs.get('file', None) is None:
                kwargs['file'] = self
            else:
                self._getattr_(kwargs['file'], 'write')

            print(*objects, **kwargs)

    def __init__(self, _getattr_=None):
        self.stream = BufferedRandom(BytesIO())
        self.position = 0

    def printer(self):
        return self.InnerSandboxInOut(self)
    
    def reader(self):
        return lambda: self.readline()
    
    def write(self, line, consumer=True):
        if not consumer:
            self.stream.seek(2) # go to the end of the stream
        else:
            self.stream.seek(0, self.position)
        self.stream.write(bytes(line, 'utf-8'))
        if consumer:
            self.position = self.stream.tell()
        
    def readline(self, consumer=True):
        if not consumer:
            self.stream.seek(2) # go to the end of the stream
        else:
            self.stream.seek(0, self.position)
        line = self.stream.readline()
        if len(line) == 0:
            return None
        if consumer:
            self.position = self.stream.tell()
        return str(line.decode('utf-8')).strip()

    def get_stream(self):
        return self.stream