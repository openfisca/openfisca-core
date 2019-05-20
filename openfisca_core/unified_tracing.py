# -*- coding: utf-8 -*-

class Frame:

    def __init__(self, name, period):
        print("new frame " + name)
        self.tracing_stack = {}
        self.name = name
        self.period = period

    def __enter__(self):
        print("enter")
        self.tracing_stack['name'] = self.name
        self.tracing_stack['period'] = self.period  

    def __exit__(self, type, value, traceback):
        print("exit")  


class SimpleTracer:

    def __init__(self):
        self.stack = {}

    def record(self, frame_name, period):
        frame = Frame(frame_name, period)
        with frame:
            if self.stack == {}:
                self.stack = frame.tracing_stack
            else:
                self.stack['children'] = frame.tracing_stack

