# -*- coding: utf-8 -*-

class Frame:

    def __init__(self, name, period):
        self.name = name
        self.period = period
        self.stack = {}

    def __enter__(self):
        self.stack['name'] = self.name
        self.stack['period'] = self.period  

    def __exit__(self, type, value, traceback):
        pass


class SimpleTracer:

    def __init__(self):
        self._stack = {}

    @property
    def stack(self):
        return self._stack

    @stack.setter
    def stack(self, stack):
        self._stack = stack

    def record(self, frame_name, period):
        frame = Frame(frame_name, period)
        with frame:
            if self.stack == {}:
                self.stack = frame.stack
            else:
                if 'children' not in self.stack:
                    self.stack['children'] = []
                self.stack['children'].append(frame.stack)
