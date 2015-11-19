# -*- coding: utf-8 -*-


class Enum(object):
    def __init__(self, varlist, start = 0):
        self._vars = {}
        self._nums = {}
        self._count = 0
        for var in varlist:
            self._vars.update({self._count + start: var})
            self._nums.update({var: self._count + start})
            self._count += 1

    def __getitem__(self, var):
        return self._nums[var]

    def __iter__(self):
        return self.itervars()

    def __len__(self):
        return self._count

    def itervars(self):
        for key, val in self._vars.iteritems():
            yield (val, key)

    def itervalues(self):
        for val in self._vars:
            yield val
