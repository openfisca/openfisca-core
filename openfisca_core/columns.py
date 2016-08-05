
class Column(object):
    def __init__(self, **kwargs):
        self.params = kwargs

    def get_params(self):
        return self.params

class BoolCol(Column):
    pass

class DateCol(Column):
    pass

class FixedStrCol(Column):
    pass

class FloatCol(Column):
    pass

class IntCol(Column):
    pass

class StrCol(Column):
    pass

class AgeCol(IntCol):
    pass

class EnumCol(IntCol):
    pass

class PeriodSizeIndependentIntCol(IntCol):
    pass
