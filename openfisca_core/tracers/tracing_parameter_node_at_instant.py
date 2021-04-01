import numpy

from openfisca_core.parameters import (
    config,
    ParameterNodeAtInstant,
    VectorialParameterNodeAtInstant,
    )


class TracingParameterNodeAtInstant:

    def __init__(self, parameter_node_at_instant, tracer):
        self.parameter_node_at_instant = parameter_node_at_instant
        self.tracer = tracer

    def __getattr__(self, key):
        child = getattr(self.parameter_node_at_instant, key)
        return self.get_traced_child(child, key)

    def __getitem__(self, key):
        child = self.parameter_node_at_instant[key]
        return self.get_traced_child(child, key)

    def get_traced_child(self, child, key):
        period = self.parameter_node_at_instant._instant_str
        if isinstance(child, (ParameterNodeAtInstant, VectorialParameterNodeAtInstant)):
            return TracingParameterNodeAtInstant(child, self.tracer)
        if not isinstance(key, str) or isinstance(self.parameter_node_at_instant, VectorialParameterNodeAtInstant):
            # In case of vectorization, we keep the parent node name as, for instance, rate[status].zone1 is best described as the value of "rate"
            name = self.parameter_node_at_instant._name
        else:
            name = '.'.join([self.parameter_node_at_instant._name, key])
        if isinstance(child, (numpy.ndarray,) + config.ALLOWED_PARAM_TYPES):
            self.tracer.record_parameter_access(name, period, child)
        return child
