# -*- coding: utf-8 -*-


class SimpleTracer:

    def __init__(self):
        self._stack = []

    @property
    def stack(self):
        return self._stack


    @stack.setter
    def stack(self, stack):
        self._stack = stack


    def enter_calculation(self, variable, period):
        self.stack.append({'name': variable, 'period': period})


    def exit_calculation(self):
        self.stack.pop()
