'''
A column is just an empty shell still used to be compatible with openfisca-core v3.

Each parameter given to the constructor is moved to the parent Variable class during variable class loading (see TaxBenefitSystem).
'''


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
