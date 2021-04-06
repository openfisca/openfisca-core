import numpy


class SimpleTracer:

    def __init__(self):
        self._stack = []

    def record_calculation_start(self, variable: str, period):
        self.stack.append({'name': variable, 'period': period})

    def record_calculation_result(self, value: numpy.ndarray):
        pass  # ignore calculation result

    def record_parameter_access(self, parameter: str, period, value):
        pass

    def record_calculation_end(self):
        self.stack.pop()

    @property
    def stack(self):
        return self._stack
