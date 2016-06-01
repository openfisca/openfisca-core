from openfisca_core.formulas import SimpleFormula, new_filled_column

class AbstractNewVariable():
	def __init__(self, name, attributes):
		self.name = name
		self.attributes = { attr_name.strip('__'): attr_value for (attr_name, attr_value) in attributes.iteritems() }


class NewVariable(AbstractNewVariable):
	def to_column(self):
		return new_filled_column(
            name = self.name,
            formula_class = SimpleFormula,
            **self.attributes
        )
