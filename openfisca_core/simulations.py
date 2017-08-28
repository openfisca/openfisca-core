# -*- coding: utf-8 -*-


import collections
import warnings
from os import linesep

import dpath

import periods
from commons import empty_clone, stringify_array


class Simulation(object):
    _parameters_at_instant_cache = None
    debug = False
    debug_all = False  # When False, log only formula calls with non-default parameters.
    period = None
    baseline_parameters_at_instant_cache = None
    stack_trace = None
    steps_count = 1
    tax_benefit_system = None
    trace = False
    traceback = None

    def __init__(
            self,
            debug = False,
            debug_all = False,
            period = None,
            tax_benefit_system = None,
            trace = False,
            opt_out_cache = False,
            simulation_json = None
            ):
        """
            If a simulation_json is given, initilalises a simulation from a JSON dictionnary.

            This way of initialising a simulation, still under experimentation, aims at replacing the initialisation from `scenario.make_json_or_python_to_attributes`.

            If no simulation_json is give, initilalises an empty simulation.
        """
        self.tax_benefit_system = tax_benefit_system
        assert tax_benefit_system is not None
        if period:
            assert isinstance(period, periods.Period)
        self.period = period

        # To keep track of the values (formulas and periods) being calculated to detect circular definitions.
        # See use in formulas.py.
        # The data structure of requested_periods_by_variable_name is: {variable_name: [period1, period2]}
        self.requested_periods_by_variable_name = {}
        self.max_nb_cycles = None

        if debug:
            self.debug = True
        if debug_all:
            assert debug
            self.debug_all = True
        if trace:
            self.trace = True
        self.opt_out_cache = opt_out_cache
        if debug or trace:
            self.stack_trace = collections.deque()
            self.traceback = collections.OrderedDict()

        # Note: Since simulations are short-lived and must be fast, don't use weakrefs for cache.
        self._parameters_at_instant_cache = {}
        self.baseline_parameters_at_instant_cache = {}

        self.instantiate_entities(simulation_json)

    def instantiate_entities(self, simulation_json):
        if simulation_json:
            check_type(simulation_json, dict, ['error'])
            allowed_entities = set(entity_class.plural for entity_class in self.tax_benefit_system.entities)
            unexpected_entities = [entity for entity in simulation_json if entity not in allowed_entities]
            if unexpected_entities:
                unexpected_entity = unexpected_entities[0]
                raise SituationParsingError([unexpected_entity],
                    'This entity is not defined in the loaded tax and benefit system. The defined entities are {}.'.format(
                        ', '.join(allowed_entities)).encode('utf-8')
                    )
            persons_json = simulation_json.get(self.tax_benefit_system.person_entity.plural, None)

            if not persons_json:
                raise SituationParsingError([self.tax_benefit_system.person_entity.plural],
                    'No {0} found. At least one {0} must be defined to run a simulation.'.format(self.tax_benefit_system.person_entity.key).encode('utf-8'))
            self.persons = self.tax_benefit_system.person_entity(self, persons_json)
        else:
            self.persons = self.tax_benefit_system.person_entity(self)

        self.entities = {self.persons.key: self.persons}
        setattr(self, self.persons.key, self.persons)  # create shortcut simulation.person (for instance)

        for entity_class in self.tax_benefit_system.group_entities:
            if simulation_json:
                entities_json = simulation_json.get(entity_class.plural)
                entities = entity_class(self, entities_json or {})
            else:
                entities = entity_class(self)
            self.entities[entity_class.key] = entities
            setattr(self, entity_class.key, entities)  # create shortcut simulation.household (for instance)

    @property
    def holder_by_name(self):
        warnings.warn(
            u"The simulation.holder_by_name attribute has been deprecated. "
            u"Please use entity.get_holder instead. "
            u"Using simulation.holder_by_name may negatively impact performances",
            Warning
            )

        result = {}
        for entity in self.entities.itervalues():
            result.update(entity._holders)
        return result

    def calculate(self, column_name, period, **parameters):
        return self.compute(column_name, period = period, **parameters).array

    def calculate_add(self, column_name, period, **parameters):
        return self.compute_add(column_name, period = period, **parameters).array

    def calculate_divide(self, column_name, period, **parameters):
        return self.compute_divide(column_name, period = period, **parameters).array

    def calculate_output(self, column_name, period):
        """Calculate the value using calculate_output hooks in formula classes."""
        if period is not None and not isinstance(period, periods.Period):
            period = periods.period(period)
        holder = self.get_variable_entity(column_name).get_holder(column_name)
        return holder.calculate_output(period)

    def clone(self, debug = False, debug_all = False, trace = False):
        """Copy the simulation just enough to be able to run the copy without modifying the original simulation."""
        new = empty_clone(self)
        new_dict = new.__dict__

        for key, value in self.__dict__.iteritems():
            if key not in ('debug', 'debug_all', 'trace'):
                new_dict[key] = value

        new.persons = self.persons.clone(new)
        setattr(new, new.persons.key, new.persons)
        new.entities = {new.persons.key: new.persons}

        for entity_class in self.tax_benefit_system.group_entities:
            entity = self.entities[entity_class.key].clone(new)
            new.entities[entity.key] = entity
            setattr(new, entity_class.key, entity)  # create shortcut simulation.household (for instance)

        if debug:
            new_dict['debug'] = True
        if debug_all:
            new_dict['debug_all'] = True
        if trace:
            new_dict['trace'] = True
        if debug or trace:
            new_dict['stack_trace'] = collections.deque()
            new_dict['traceback'] = collections.OrderedDict()

        return new

    def compute(self, column_name, period, **parameters):
        if period is not None and not isinstance(period, periods.Period):
            period = periods.period(period)
        if (self.debug or self.trace) and self.stack_trace:
            variable_infos = (column_name, period)
            calling_frame = self.stack_trace[-1]
            caller_input_variables_infos = calling_frame['input_variables_infos']
            if variable_infos not in caller_input_variables_infos:
                caller_input_variables_infos.append(variable_infos)
        holder = self.get_variable_entity(column_name).get_holder(column_name)
        result = holder.compute(period = period, **parameters)
        return result

    def compute_add(self, column_name, period, **parameters):
        if period is not None and not isinstance(period, periods.Period):
            period = periods.period(period)
        if (self.debug or self.trace) and self.stack_trace:
            variable_infos = (column_name, period)
            calling_frame = self.stack_trace[-1]
            caller_input_variables_infos = calling_frame['input_variables_infos']
            if variable_infos not in caller_input_variables_infos:
                caller_input_variables_infos.append(variable_infos)
        holder = self.get_variable_entity(column_name).get_holder(column_name)
        return holder.compute_add(period = period, **parameters)

    def compute_divide(self, column_name, period, **parameters):
        if period is not None and not isinstance(period, periods.Period):
            period = periods.period(period)
        if (self.debug or self.trace) and self.stack_trace:
            variable_infos = (column_name, period)
            calling_frame = self.stack_trace[-1]
            caller_input_variables_infos = calling_frame['input_variables_infos']
            if variable_infos not in caller_input_variables_infos:
                caller_input_variables_infos.append(variable_infos)
        holder = self.get_variable_entity(column_name).get_holder(column_name)
        return holder.compute_divide(period = period, **parameters)

    def get_array(self, column_name, period):
        if period is not None and not isinstance(period, periods.Period):
            period = periods.period(period)
        if (self.debug or self.trace) and self.stack_trace:
            variable_infos = (column_name, period)
            calling_frame = self.stack_trace[-1]
            caller_input_variables_infos = calling_frame['input_variables_infos']
            if variable_infos not in caller_input_variables_infos:
                caller_input_variables_infos.append(variable_infos)
        return self.get_variable_entity(column_name).get_holder(column_name).get_array(period)

    def _get_parameters_at_instant(self, instant):
        parameters_at_instant = self._parameters_at_instant_cache.get(instant)
        if parameters_at_instant is None:
            parameters_at_instant = self.tax_benefit_system.get_parameters_at_instant(instant)
            self._parameters_at_instant_cache[instant] = parameters_at_instant
        return parameters_at_instant

    def get_holder(self, column_name, default = UnboundLocalError):
        warnings.warn(
            u"The simulation.get_holder method has been deprecated. "
            u"Please use entity.get_holder instead.",
            Warning
            )
        column = self.tax_benefit_system.get_column(column_name, check_existence = True)
        entity = self.entities[column.entity.key]
        holder = entity._holders.get(column_name)
        if holder:
            return holder
        if default is UnboundLocalError:
            raise KeyError(column_name)
        return default

    def get_or_new_holder(self, column_name):
        warnings.warn(
            u"The simulation.get_or_new_holder method has been deprecated. "
            u"Please use entity.get_holder instead.",
            Warning
            )
        column = self.tax_benefit_system.get_column(column_name, check_existence = True)
        entity = self.get_entity(column.entity)
        return entity.get_holder(column_name)

    def _get_baseline_parameters_at_instant(self, instant):
        baseline_parameters_at_instant = self._baseline_parameters_at_instant_cache.get(instant)
        if baseline_parameters_at_instant is None:
            baseline_parameters_at_instant = self.tax_benefit_system._get_baseline_parameters_at_instant(
                instant = instant,
                traced_simulation = self if self.trace else None,
                )
            self.baseline_parameters_at_instant_cache[instant] = baseline_parameters_at_instant
        return baseline_parameters_at_instant

    def graph(self, column_name, edges, get_input_variables_and_parameters, nodes, visited):
        self.get_variable_entity(column_name).get_holder(column_name).graph(edges, get_input_variables_and_parameters, nodes, visited)

    def parameters_at(self, instant, use_baseline = False):
        if isinstance(instant, periods.Period):
            instant = instant.start
        assert isinstance(instant, periods.Instant), "Expected an Instant (e.g. Instant((2017, 1, 1)) ). Got: {}.".format(instant)
        if use_baseline:
            return self._get_baseline_parameters_at_instant(instant)
        return self._get_parameters_at_instant(instant)

    def find_traceback_step(self, variable_name, period):
        assert isinstance(period, periods.Period), period
        column = self.tax_benefit_system.get_column(variable_name, check_existence=True)
        step = self.traceback.get((variable_name, period))
        if step is None and column.is_period_size_independent:
            period = None
        step = self.traceback.get((variable_name, period))
        return step

    def stringify_variable_for_period_with_array(self, variable_name, period):
        holder = self.get_variable_entity(variable_name).get_holder(variable_name)
        return u'{}@{}<{}>{}'.format(
            variable_name,
            holder.entity.key,
            str(period),
            stringify_array(holder.get_array(period)),
            )

    def stringify_input_variables_infos(self, input_variables_infos):
        return u', '.join(
            self.stringify_variable_for_period_with_array(
                variable_name=input_variable_name,
                period=input_variable_period,
                )
            for input_variable_name, input_variable_period in input_variables_infos
            )

    # Fixme: to rewrite
    def to_input_variables_json(self):
        return None

    def get_variable_entity(self, variable_name):
        column = self.tax_benefit_system.get_column(variable_name, check_existence = True)
        return self.get_entity(column.entity)

    def get_entity(self, entity_type = None, plural = None):
        if entity_type:
            return self.entities[entity_type.key]
        if plural:
            return [entity for entity in self.entities.values() if entity.plural == plural][0]


def check_type(input, type, path = []):
    json_type_map = {
        dict: "Object",
        list: "Array",
        basestring: "String"
        }

    if not isinstance(input, type):
        raise SituationParsingError(path,
            'Invalid type: must be of type "{}".'.format(json_type_map[type]))


class SituationParsingError(Exception):
    def __init__(self, path, message, code = None):
        self.error = {}
        dpath_path = '/'.join(path)
        message = message.strip(linesep).replace(linesep, ' ')
        dpath.util.new(self.error, dpath_path, message)
        self.code = code
        Exception.__init__(self, self.error)
