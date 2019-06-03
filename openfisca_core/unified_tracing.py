# -*- coding: utf-8 -*-

class Frame:

    def __init__(self, name, period):
        self.name = name
        self.period = period
        self.stack = {}

    def __enter__(self):
        # to json
        self.stack['name'] = self.name
        self.stack['period'] = self.period  

    def __exit__(self, type, value, traceback):
        print(self.stack)
        self.stack = {}




class SimpleTracer:

    def __init__(self):
        self._stack = {}

    @property
    def stack(self):
        return self._stack

    @stack.setter
    def stack(self, stack):
        self._stack = stack


    def new_frame(self, variable, period):
        return Frame(variable, period)


    def record(self, variable, period):
        frame = self.new_frame(variable, period)
        with frame:
            if self.stack == {}:
                print("nouvelle stack")
                self.stack.update(frame.stack)
                print(frame.stack)
            else:
                print("ajout à stack existante")
                if 'children' not in self.stack:
                    self.stack['children'] = []
                self.stack['children'].append(frame.stack)
