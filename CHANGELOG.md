# Changelog

### 23.1.1 [#661](https://github.com/openfisca/openfisca-core/pull/661)

- Fixup Python 3 compatibility

### 23.1.0 [#660](https://github.com/openfisca/openfisca-core/pull/660)

Make package compatible with Python 3

### 23.0.2 [#645](https://github.com/openfisca/openfisca-core/pull/645)

Start adapting OpenFisca to Python 3
- Imports are now all absolute imports
- `unicode_type` and `basestring_type` are now used for compatible type checking.
- All calls for sorted() use the key parameter
- Iteration on dict now uses dict.items()

### 23.0.1 [656](https://github.com/openfisca/openfisca-core/pull/656)

* Re-accept `int` values for `instant` in `tax_benefit_system.get_parameter_at_instant(instant)`
  * `int` values were accidently rejected since v23

# 23.0.0 [643](https://github.com/openfisca/openfisca-core/pull/643)

This changeset aims at simplifying the OpenFisca Core architecture.

Changes should be transparent for legislation modeling and web API usage.

It can impact users using the Python API (see Breaking changes part)

General architecture principles:
  - `Simulation` is the class in charge of running the calculations
  - `Holder` is the class in charge of keeping input and previously calculated values

#### Breaking changes

- Remove two (already deprecated) possible values for the variable attribute `base_function`:
  - `permanent_default_value`
  - `requested_period_added_value`

In `Holder`:
  - Remove deprecated constructor `Holder(simulation, variable)`
    - Use `Holder(entity, variable)` instead
  - Remove attributes:
    - `formula` and `real_formula`
      - Use `variable.formulas` instead (see more further down)
    - `array`
      - Use `get_array(period)` instead
  - Remove methods:
    - `calculate` and `compute`
      - Use `simulation.calculate` instead
    - `calculate_output`
      - Use `simulation.calculate_output` instead
    - `compute_add`
      - Use `simulation.calculate_add` instead
    - `compute_divide`
      - Use `simulation.calculate_divide` instead
    - `get_from_cache`
      - Use `get_array` instead
    - `graph`
  - Methods `set_input` and `put_in_cache` don't return anything anymore.

In `Simulation`:
  - Reorder constructor arguments
    - `tax_benefit_system` is now the first (mandatory) argument, and `simulation_json` the second (optional) one.
  - Remove attributes:
    - `holder_by_name`
      - Use `simulation.get_holder(...)` or `entity.get_holder(...)` instead
  - Remove methods:
    - `compute`
      - Use `calculate` instead
    - `compute_add`
      - Use `calculate_add` instead
    - `compute_divide`
        - Use `calculate_divide` instead
    - `parameters_at`
      - Use `simulation.tax_benefit_sytem.get_parameters_at_instant` instead
    - `graph`
    - `to_input_variables_json`
  - Undeprecate, but slightly change the behaviour of the `get_holder(variable)` method:
    - Optional second argument `default` is not accepted anymore
    - If no holder has yet been created for the variable, no error is raised, and a new holder is created and returned.

#### New features

- Introduce `variable.formulas`, a sorted dict containing all the formulas of a variable:

```py
tax_benefit_system.get_variable('basic_income').formulas
>>> SortedDict({
    '2015-12-01': <function formula_2015_12 at 0x1079aa500>,
    '2016-12-01': <function formula_2016_12 at 0x1079aa488>
    })
```

Each value is a simple python function.

- Make `holder.set_input` more flexible
  - It now accepts a string as `period`
  - It now accepts a list as `array`

#### Technical changes

- Remove module `formulas` and class `Formula`
  - Variables's formulas are now simple functions.
- Remove class `DatedHolder`
  - All calculation methods now return a simple numpy array
- Variables don't necessary have a base function anymore
  - Without a base function, the default behavior is to return the default value if there is no formula.

## 22.1.0 [#648](https://github.com/openfisca/openfisca-core/pull/648)

* Allow two variable file to have the same name in a tax and benefit system
  - A [collision](https://github.com/openfisca/openfisca-core/issues/642) between module names made it impossible so far.

### 22.0.10 [#654](https://github.com/openfisca/openfisca-core/pull/654)

* Fix `dtype` attribute for `EnumArray`s (returned when calculating a variable of `value_type` `Enum`):
  - It was the type `np.int16` and not the dtype instance `np.dtype(np.int16)`
  - This caused issue when trying to export an `EnumArray` with `pandas`

### 22.0.9 [#650](https://github.com/openfisca/openfisca-core/pull/5O)

* Fix operators such as `household.first_parent`, `foyer_fiscal.declarant_principal` for multi-entities simulations.
  - This issue was not affecting simulations with several persons in a _single_ entity
  - The underlying `entity.value_from_person` operator was not working as expected in case the persons of the simulation were not sorted by entity id in the persons vector (see example in 22.0.8 right below).

### 22.0.8 [#646](https://github.com/openfisca/openfisca-core/pull/639)

* Fix `entity.max`, `entity.min`, `entity.all` and `entity.reduce` for multi-entities simulations.
  - This issue was not affecting simulations with several persons in a _single_ entity
  - These operators were not working as expected in case the persons of the simulation were not sorted by entity id in the persons vector. For instance:
    - First household: [Alice, Bob]
    - Second household: [Cesar]
    - Persons vector: [Alice, Cesar, Bob]

### 22.0.7 [#639](https://github.com/openfisca/openfisca-core/pull/639)

* Update CircleCI configuration to its v2

### 22.0.6 [#642](https://github.com/openfisca/openfisca-core/pull/642)

* Improve parameters performances

### 22.0.5 [#639](https://github.com/openfisca/openfisca-core/pull/639)

* Update country-template dependency to >= 3.0.0, < 4.0.0

### 22.0.4 [#624](https://github.com/openfisca/openfisca-core/pull/624)

* Technical improvement:
* Details:
  - Make sure ParameterNode:__repr__ generates a valid YAML representation

### 22.0.3 [#635](https://github.com/openfisca/openfisca-core/pull/635)

* Update numpy dependency
* Details:
  - Previously, openfisca-core used features removed on numpy 1.13

### 22.0.2 [#627](https://github.com/openfisca/openfisca-core/pull/627) [#593](https://github.com/openfisca/openfisca-core/pull/593)

- Update openfisca_serve [rst](http://openfisca.readthedocs.io/en/latest/openfisca_serve.html) documentation
  * Make native gunicorn parameters use in `openfisca serve` obvious and make parameters' format more explicit

### 22.0.1 [#628](https://github.com/openfisca/openfisca-core/pull/628)

- Fix a bug that broke the route `calculate` of the legacy web API since `21.0.2`

# 22.0.0 [#602](https://github.com/openfisca/openfisca-core/pull/602)

#### Breaking changes

- Improve entities projection consistency

Before, there were inconsistencies in the behaviors of projectors:

_For instance, for a simulation that contains 4 persons in 1 household:_

```py
person.household('rent', '2018-02')  # The rent paid by the household of the person.
>>> [800, 800, 800, 800]  # Has the dimension of persons (4)

salaries = person.household.members('salary', '2018-02')
sum_salary = person.household.sum(salaries)  # The sum of the salaries of the person's family
>>> [4000] Has the dimension of household (1)
```


Now, consistency have been enforced for all entities related helpers (`sum`, `min`, `max`, `all`, `any`, `has_role`, etc.)


```py
person.household('rent', '2018-02')  # The rent paid by the household of the person.
>>> [800, 800, 800, 800]  # Has the dimension of persons (4)

salaries = person.household.members('salary')
sum_salary = person.household.sum(salaries)  # The sum of the salaries of the person's family
>>> [4000, 4000, 4000, 4000]  # Has the dimension of persons (4)
```

This is a breaking change, as all the adaptations (such as [this one](https://github.com/openfisca/openfisca-france/blob/18.11.0/openfisca_france/model/prestations/minima_sociaux/rsa.py#L375-L376)) used to overcome these inconsistensies must be removed.

## 21.5.0 [#621](https://github.com/openfisca/openfisca-core/pull/621)

- Introduce:
  - [`person.get_rank(entity, criteria, condition)`](https://github.com/openfisca/openfisca-core/blob/21.4.0/openfisca_core/entities.py#L278-L293)
  - [`entity.value_nth_person(k, array, default)`](https://github.com/openfisca/openfisca-core/blob/21.4.0/openfisca_core/entities.py#L515-L520)

## 21.4.0 [#603](https://github.com/openfisca/openfisca-core/pull/603)

#### New features

- Improve `Tracer`:
  - Make aggregation more efficient
  - Introduce [`tracer.print_trace`](http://openfisca.readthedocs.io/en/latest/tracer.html#openfisca_core.tracers.Tracer.print_trace)

### 21.3.6 [#616](https://github.com/openfisca/openfisca-core/pull/618)

- Describe `/spec` endpoint in OpenAPI documentation available at `/spec`

### 21.3.5 [#620](https://github.com/openfisca/openfisca-core/pull/620)

* Technical improvement:
* Details:
  - Adapt to version `2.1.0` of Country-Template and version `1.1.3` of Extension-Template.

### 21.3.4 [#604](https://github.com/openfisca/openfisca-core/pull/604)

- Introduce [simulation generator](http://openfisca.readthedocs.io/en/latest/simulation_generator.html)

### 21.3.3 [#608](https://github.com/openfisca/openfisca-core/pull/608)

- Improve API response time

### 21.3.2 [#617](https://github.com/openfisca/openfisca-core/pull/611)

- Make decompositions more robust

### 21.3.1 [#617](https://github.com/openfisca/openfisca-core/pull/617)

- Fix bug on API `/variable/{id}`
  - Encode API `/variable/{id}` output to `utf-8`
  - Add tests for `/variable/{id}` and `/parameter/{id}` encoding

## 21.3.0 [#610](https://github.com/openfisca/openfisca-core/pull/610)

Add `--only-variables` and `--ignore-variables` options to `openfisca-run-test` to filter out tested output variables if needed.

### 21.2.2 [#612](https://github.com/openfisca/openfisca-core/pull/612)

- When a variable file is loaded twice in the same python interpreter, make sure the second loading doesn't corrupt the first one.
    - This fixes a bug introduced in 21.0.2, which could lead to a corruption of the tax and benefit in rare edge cases

### 21.2.1 [#613](https://github.com/openfisca/openfisca-core/pull/613)

- Fix two bugs that appeared with 21.2.0:
  - Properly encode the result of a formula returning an Enum value
  - Enable storing an Enum value on disk

## 21.2.0 [#601](https://github.com/openfisca/openfisca-core/pull/601)

#### New features

- Improve [`holder.get_memory_usage`]((http://openfisca.readthedocs.io/en/latest/holder.html#openfisca_core.holders.Holder.get_memory_usage)):
  - Add `nb_requests` and `nb_requests_by_array` fields in the memory usage stats for traced simulations.

- Enable intermediate data storage on disk to avoid memory overflow
  - Introduce `memory_config` option in `Simulation` constructor
    - This allows fine tuning of memory management in OpenFisca

For instance:

```
from openfisca_core.memory_config import MemoryConfig
config = MemoryConfig(
    max_memory_occupation = 0.95,  # When 95% of the virtual memory is full, switch to disk storage
    priority_variables = ['salary', 'age']  # Always store these variables in memory
    variables_to_drop = ['age_elder_for_family_benefit']  # Do not store the value of these variables
    )
```

## 21.1.0 [#598](https://github.com/openfisca/openfisca-core/pull/598)

#### New features

- Improve `Tracer`:

  - Introduce an `aggregate` option in [`tracer.print_computation_log`](http://openfisca.readthedocs.io/en/latest/tracer.html#openfisca_core.tracers.Tracer.print_computation_log) to handle large population simulations.
  - Introduce [`tracer.usage_stats`](http://openfisca.readthedocs.io/en/latest/tracer.html#openfisca_core.tracers.Tracer.usage_stats) to keep track of the number of times a variable is computed.

- Introduce methods to keep track of memory usage:

  - Introduce [`holder.get_memory_usage`](http://openfisca.readthedocs.io/en/latest/holder.html#openfisca_core.holders.Holder.get_memory_usage)
  - Introduce `entity.get_memory_usage`
  - Introduce `simulation.get_memory_usage`

- Improve `Holder` public interface:

  - Enhance [`holder.delete_arrays`](http://openfisca.readthedocs.io/en/latest/holder.html#openfisca_core.holders.Holder.get_memory_usage) to be able to remove known values only for a specific period
  - Introduce [`holder.get_known_periods`](http://openfisca.readthedocs.io/en/latest/holder.html#openfisca_core.holders.Holder.get_known_periods)

- Introduce [`variable.get_formula`](http://openfisca.readthedocs.io/en/latest/variables.html#openfisca_core.variables.Variable.get_formula)

- Re-introduce `taxscales.combine_tax_scales` to combine several tax scales.

#### Deprecations

- Deprecate `requested_period_added_value` base function, as it had no effect.

### 21.0.3 [#595](https://github.com/openfisca/openfisca-core/pull/595)

#### Bug fix

- Fix API response encoding from ascii to utf-8
  * Improve user message by displaying `UnicodeDecodeError` information

# 21.0.2 [#589](https://github.com/openfisca/openfisca-core/pull/589) [#600](https://github.com/openfisca/openfisca-core/pull/600) [#605](https://github.com/openfisca/openfisca-core/pull/605)

_Note: the 21.0.1 and 21.0.0 versions have been unpublished due to performance issues_

#### Breaking changes

##### Change the way enumerations (Enum) are defined when coding variables

Before:

```py
HOUSING_OCCUPANCY_STATUS = Enum([
    u'Tenant',
    u'Owner',
    u'Free lodger',
    u'Homeless'])
```

Now:

```py
class HousingOccupancyStatus(Enum):
    tenant = u'Tenant'
    owner = u'Owner'
    free_lodger = u'Free lodger'
    homeless = u'Homeless'
```

> Each Enum item has:
> - a `name` property that contains its key (e.g. `tenant`)
> - a `value` property that contains its description (e.g. `"Tenant or lodger who pays a monthly rent"`)

- Enum variables must now have an explicit default value

```py
class housing_occupancy_status(Variable):
    possible_values = HousingOccupancyStatus,
    default_value = HousingOccupancyStatus.tenant
    entity = Household
    definition_period = MONTH
    label = u"Legal housing situation of the household concerning their main residence"
```


- In a formula, to compare an Enum variable to a fixed value, use `housing_occupancy_status == HousingOccupancyStatus.tenant`

- To access a parameter that has a value for each Enum item (e.g. a value for `zone_1`, a value for `zone_2` ... ), use fancy indexing

> For example, if there is an enum:
> ```py
>     class TypesZone(Enum):
>         z1 = "Zone 1"
>         z2 = "Zone 2"
> ```
> And two parameters `parameters.city_tax.z1` and `parameters.city_tax.z2`, they can be dynamically accessed through:
> ```py
> zone = np.asarray([TypesZone.z1, TypesZone.z2, TypesZone.z2, TypesZone.z1])
> zone_value = parameters.rate._get_at_instant('2015-01-01').single.owner[zone]
> ```
> returns
> ```py
> [100, 200, 200, 100]
> ```
>

##### Change the simulation inputs and outputs for enumeration variables

###### Web API and YAML tests

- When setting the value of an input Enum variable for a simulation, the user must now send the **string identifier** (e.g. `free_lodger`).
   - The item index (e.g. `2`) is not accepted anymore
   - The value (e.g. `Free lodger`) is not accepted anymore.

- When calculating an Enum variable through the web API, the output will now be the string identifier.

###### Python API

- When using the Python API (`set_input`), the three following inputs are accepted:
   - The enum item (e.g. HousingOccupancyStatus.tenant)
   - The enum string identifier (e.g. "tenant")
   - The enum item index, though this is not recommanded.
     - If you rely on index, make sure to specify an `__order__` attribute to all your enums to make sure each intem has the right index. See the enum34 [doc](https://pypi.python.org/pypi/enum34/1.1.1).

> Example:
```py
holder = simulation.household.get_holder('housing_occupancy_status')
# Three possibilities
holder.set_input(period, np.asarray([HousingOccupancyStatus.owner]))
holder.set_input(period, np.asarray(['owner']))
holder.set_input(period, np.asarray([0])) # Highly not recommanded
```

- When calculating an Enum variable, the output will be an [EnumArray](http://openfisca.readthedocs.io/en/latest/enum_array.html#module-openfisca_core.indexed_enums).

# 20.0.0 [#590](https://github.com/openfisca/openfisca-core/pull/590)

#### Breaking changes

##### Change the way Variables are declared

- Replace `column` attribute by `value_type`
  * Possible values of `value_type` are:
    * `int`
    * `float`
    * `bool`
    * `str`
    * `date`
    * `Enum`

Before:

```py
class basic_income(Variable):
    column = FloatCol
    entity = Person
    definition_period = MONTH
    label = "Basic income provided to adults"
```

Now:

```py
class basic_income(Variable):
    value_type = float
    entity = Person
    definition_period = MONTH
    label = "Basic income provided to adults"
```

- `default_value` is now a `Variable` attribute

Before:

```py
class is_citizen(Variable):
    column = BoolCol(default = True)
    entity = Person
    definition_period = MONTH
    label = "Whether the person is a citizen"
```

Now:

```py
class is_citizen(Variable):
    value_type = bool
    default_value = True
    entity = Person
    definition_period = MONTH
    label = "Whether the person is a citizen"
```

- For `Variables` which `value_type` is `str`, `max_lentgh` is now an attribute

Before:

```py
class zipcode(Variable):
    column = FixedStrCol(max_length = 5)
    entity = Menage
    label = u"Code INSEE (depcom) du lieu de résidence"
    definition_period = MONTH
```

After:

```py
class zipcode(Variable):
    value_type = str
    max_length = 5
    entity = Menage
    label = u"Code INSEE (depcom) du lieu de résidence"
    definition_period = MONTH
```

- For `Variables` which `value_type` is `Enum`, `possible_values` is now an attribute:

Before:

```py
class housing_occupancy_status(Variable):
    column = EnumCol(
        enum = Enum([
            u'Tenant',
            u'Owner',
            u'Free lodger',
            u'Homeless'])
        )
    entity = Household
    definition_period = MONTH
    label = u"Legal housing situation of the household concerning their main residence"
```

After:

```py
class housing_occupancy_status(Variable):
    value_type = Enum
    possible_values = Enum([
        u'Tenant',
        u'Owner',
        u'Free lodger',
        u'Homeless'
        ])
    entity = Household
    definition_period = MONTH
    label = u"Legal housing situation of the household concerning their main residence"
```

- Remove `PeriodSizeIndependentIntCol`:
  * Replaced by `Variable` attribute `is_period_size_independent`


##### Deprecate `Column`

`Column` are now considered deprecated. Preferably use `Variable` instead.

If you do need a column for retro-compatibility, you can use:

```py
from openfisca_core.columns import make_column_from_variable

column = make_column_from_variable(variable)
```


- In `TaxBenefitSystem`:
  * Remove `neutralize_column` (deprecated since `9.1.0`, replaced by `neutralize_variable`)
  * Rename `column_by_name` to `variables`
  * Rename `get_column` to `get_variable`
  * Remove `update_column`
  * Remove `add_column`
  * Remove `automatically_loaded_variable` (irrelevant since conversion columns have been removed)
  * Move `VariableNotFound` to `errors` module


- In `Holder`:
  * Rename `holder.column` to `holder.variable`

- In `Column`:
  * `Column` should only be instantiated using `make_column_from_variable`. Former constructors do not work anymore.
  * Remove `column.start`, which was `None` since `14.0.0`
  * Replace `column.formula_class` by `variable.formula`
  * Replace `column.enum` by `variable.possible_values`
  * Replace `column.default` by `variable.default_value`

- In `formulas`:
  * Rename `get_neutralized_column` to `get_neutralized_variable`
  * Remove `new_filled_column`

- In `Variable`:
  * Remove `to_column`
  * Variables can now directly be instanciated:

```py
class salary(Variable):
    entity = Person
    ...


salary_variable = salary()
```

You can learn more about `Variable` by checking its [reference documentation](http://openfisca.readthedocs.io/en/latest/variables.html).

# 19.0.0 [#583](https://github.com/openfisca/openfisca-core/pull/583)
> Wrongfully published as 18.2.0

#### Breaking changes

- Change the way the API is started
  * The previous command `COUNTRY_PACKAGE=openfisca_country gunicorn ...` does not work anymore
  * The new command to serve the API is `openfisca serve`.
    * Read more in the [doc](https://openfisca.readthedocs.io/en/latest/openfisca_serve.html)
    * This command allows to serve reforms and extensions in the new API

- In `openfisca-run-test` and `openfisca-serve`, rename option `--country_package` to `--country-package`

## 18.1.0 [#578](https://github.com/openfisca/openfisca-core/pull/578)

#### New features

- Improve the representations of parameters when navigating the legislation in Python.

For instance:
```
tax_benefit_system.parameters.benefits

>>> basic_income:
>>>   2015-12-01: 600.0
>>> housing_allowance:
>>>   2016-12-01: None
>>>   2010-01-01: 0.25

tax_benefit_system.parameters.benefits.basic_income

>>>2015-12-01: 600.0
```

- Request parameter at a given date with the `parameters.benefits('2015-07-01')` notation.

- Be more flexible about parameters definitions

The two following expressions are for instance striclty equivalent:

```
Parameter("taxes.rate", {"2015-01-01": 2000})
Parameter("taxes.rate", {"values": {"2015-01-01":{"value": 2000}}})
```

- Make sure `parameters.benefits('2015-07-01')` and `parameters.benefits('2015-07')` return the same value.
- Raise an error when calling `parameters.benefits('invalid_key')`.
- Improve errors when `parameter.update` is used with wrong arguments

#### Deprecations

- Deprecate `ValuesHistory` class. Use `Parameter` instead.
- Deprecate `parameter.values_history`. Just use `parameter` instead.

### 18.0.2 [#585](https://github.com/openfisca/openfisca-core/pull/585)

- Track the real visitor IP in the web API
  - Handle the nginx proxy

### 18.0.1 [#584](https://github.com/openfisca/openfisca-core/pull/584)

- Add a link in `openAPI.yml` to the OpenFisca documentation page explaining the web API inputs and outputs for the /calculate route.

## 18.0.0 [#582](https://github.com/openfisca/openfisca-core/pull/582)

#### New features

Add tracing to get details about all the intermediate calculations of a simulation

- Introduce new Web API route `/trace` to get a simulation's detailed calculation steps
  - See the [swagger documentation for OpenFisca-France](https://legislation.openfisca.fr/swagger)

- Introduce `simulation.tracer.print_computation_log` to print a simulation's detailed calculation steps
  - This is available if the `trace` argument has been set to `True` in the `Simulation` constructor.
  - See the [reference documentation](https://openfisca.readthedocs.io/en/latest/tracer.html) about the tracer.

_Warning: Both of these features are still currently under experimentation. You are very welcome to use them and send us precious feedback, but keep in mind that the way they are used and the results they give might change without any major version bump._

#### Breaking changes

- Deprecate and remove:
  - `simulation.traceback`
  - `simulation.stack_trace`
  - `simulation.find_traceback_step`
  - `simulation.stringify_input_variables_infos`
  - `simulation.stringify_variable_for_period_with_array`

- Remove argument `debug_all` from:
  - `Scenario.new_simulation` method
  - `Simulation` constructor

### 17.2.1 [#581](https://github.com/openfisca/openfisca-core/pull/581)

- Add the possibility to track API visitor's IP

## 17.2.0 [#570](https://github.com/openfisca/openfisca-core/pull/570)

- Enable to calculate parameters according to a variable

For instance, if a parameter `rate` depends on a variable `zone` that can take the values `z1` or `z2`:

In `rate.yaml`:

```
z1:
  values:
    '2015-01-01':
      value: 100
z2:
  values:
    '2015-01-01':
      value: 200
```

Then it is now possible to use:

```
zone = household('zone', period)
rate = parameters(period).rate[zone]
```


For more information, check the [documentation](http://openfisca.org/doc/coding-the-legislation/legislation_parameters.html#computing-a-parameter-that-depends-on-a-variable-fancy-indexing)

### 17.1.2 [#569](https://github.com/openfisca/openfisca-core/pull/569)

- Fix migration script `xml_to_yaml.py`
  - The attributes `reference` of nodes `END`, `VALUE`, `PLACEHOLDER`, `BAREME`, `TRANCHE`, `ASSIETTE`, `TAUX`, `MONTANT`, `SEUIL` were not parsed. Now they are parsed to YAML.

### 17.1.1

- Reference the new address of the documentation

## 17.1.0

- Allow to document entities and entities roles
  - Add attribute `Entity.doc` (e.g. `Household.doc`)
  - Add attribute `Role.doc` (e.g. `Household.CHILD.doc`)

### 17.0.1

#### Minor Change

- Handle the case where the user accidentally puts a coma at the end of a variable reference so it has no consequence on the API output.
- All variable references are transformed into lists of strings.

# 17.0.0 - [#552](https://github.com/openfisca/openfisca-core/pull/552)

#### Breaking changes

##### Parameter files

* Load the legislation parameters from a directory `parameters` containing YAML files, instead of XML files

  Before:
  ```XML
  <NODE code="root">
    <NODE code="impot">
      <CODE code="taux" description="" format="percent">
        <END deb="2016-01-01"/>
        <VALUE deb="2015-01-01" valeur="0.32" />
        <VALUE deb="1998-01-01" valeur="0.3" />
      </CODE>
    </NODE>
  </NODE>
  ```

  Now:
  ```yaml
  impot:
    taux:
      description: Taux d'impôt sur les salaires
      unit: /1
      values:
        2016-01-01:
          value: null
        2015-01-01:
          value: 0.32
        1991-01-01:
          value: 0.3
  ```

  - The XML attributes `format` and `type` are replaced by the YAML attribute `unit`, which is a free text field.

##### reforms

* Rename `Reform.modify_legislation_json()` -> `Reform.modify_parameters()`
* Remove `reforms.compose_reforms()`.
* Remove `reforms.update_legislation()`.
  - To modify an existing parameter, use `ValuesHistory.update()` instead.
  - You can navigate the parameters using `.` (e.g. `parameters.taxes.tax_on_salaries.public_sector.rate`)
  - Before:
    ```python
    new_legislation_parameters = update_legislation(
        legislation_json = original_legislation_parameters,
        path = ('children', 'impot_revenu', 'children', 'bareme', 'brackets', 1, 'threshold'),
        period = reform_period,
        value = 6011,
        )
    ```
  - Now:
    ```python
    parameters.impot_revenu.bareme[1].threshold.update(period = reform_period, value = 6011)
    ```

* Change the syntax to dynamically create new parameters
  - Before :
    ```python
    reform_legislation_subtree = {
        "@type": "Node",
        "description": "PLF 2016 sur revenus 2015",
        "children": {
            "decote_seuil_celib": {
                "@type": "Parameter",
                "description": "Seuil de la décôte pour un célibataire",
                "format": "integer",
                "unit": "currency",
                "values": [
                    {'start': u'2016-01-01', },
                    {'start': u'2015-01-01', 'value': round(1135 * (1 + inflation))},
                    ],
                },
            "decote_seuil_couple": {
                "@type": "Parameter",
                "description": "Seuil de la décôte pour un couple",
                "format": "integer",
                "unit": "currency",
                "values": [
                    {'start': u'2065-01-01', },
                    {'start': u'2015-01-01', 'value': round(1870 * (1 + inflation))},
                    ],
                },
            },
        }
    reference_legislation_copy['children']['plf2016_conterfactual'] = reform_legislation_subtree
    ```

  - Now:
    ```python
    from openfisca_core.parameters import ParameterNode

    inflation = .001
    reform_parameters_subtree = ParameterNode('plf2016_conterfactual', data = {
        'decote_seuil_celib': {
          'values': {
            "2015-01-01": {'value': round(1135 * (1 + inflation))},
            "2016-01-01": {'value': None}
            }
          },
        'decote_seuil_couple': {
          'values': {
            "2015-01-01": {'value': round(1870 * (1 + inflation))},
            "2065-01-01": {'value': None}
            }
          },
        })
    reference_parameters.add_child('plf2016_conterfactual', reform_parameters_subtree)
    ```

  - Note that this way of creating parameters is only recommanded when using dynamically computed values (for instance `round(1135 * (1 + inflation))` in the previous example). If the values are static, the new parameters can be directly built from YAML (See New features section).

##### TaxBenefitSystem

* Remove parameter `legislation_json` in constructor
* Remove methods/attributes:
  - `compact_legislation_by_instant_cache`
  - `get_baseline_compact_legislation`
  - `compute_legislation`
  - `get_legislation`
    + We can now directly use the `parameters` attribute.
* Rename
  - `preprocess_legislation` -> `preprocess_parameters`
  - `add_legislation_params` -> `load_parameters`
  - `get_compact_legislation` -> `get_parameters_at_instant`
    + The signature of the method has changed. Check the [documentation](http://openfisca.readthedocs.io/en/latest/tax-benefit-system.html#openfisca_core.taxbenefitsystems.TaxBenefitSystem.load_parameters).

##### Simulation

* Remove methods/attributes:
  - `compact_legislation_by_instant_cache`
  - `get_baseline_compact_legislation`
* Rename
    `baseline_compact_legislation_by_instant_cache` -> `baseline_parameters_at_instant_cache`
    `legislation_at` -> `parameters_at`

#### New features

* In reforms, new parameters can be added from a YAML file.
  - The function `parameters.load_parameter_file()` loads a YAML file.
  - The function `ParameterNode.add_child()` adds a new child to an existing legislation node.
  - Example:
    ```python
    import os
    from openfisca_core.parameters import load_parameter_file

    dir_path = os.path.dirname(__file__)

    def reform_modify_parameters(parameters):
        file_path = os.path.join(dir_path, 'plf2016.yaml')
        reform_parameters_subtree = load_parameter_file(name = 'plf2016', file_path=file_path)
        parameters.add_child('plf2016', reform_parameters_subtree)
        return parameters

    ...
    ```

* In module model_api, add classes that are needed to build reforms:
  - `load_parameter_file`
  - `ParameterNodeNode`
  - `Scale`
  - `Bracket`
  - `Parameter`
  - `ValuesHistory`
  - `periods.period`.


#### Technical changes

* Refactor the internal representation and the interface of legislation parameters
  - The parameters of a legislation are wraped into the classes `Node`, `Parameter`, `Scale`, `Bracket`, `ValuesHistory`, `ValueAtInstant` instead of bare python dict.
  - The parameters of a legislation at a given instant are wraped into the classes `NodeAtInstant`, `ValueAtInstant` and tax scales instead of bare python objects.
  - The file `parameters.py` and the classes defined inside are responsible both for loading and accessing the parameters. Before the loading was implemented in `legislationsxml.py` and the other processings were implemented in `legislations.py`
  - The validation of the XML files was performed against a XML schema defined in `legislation.xsd`. Now the YAML files are loaded with the library `yaml` and then validated in basic Python.

* The word "legislation" is replaced by the word "parameters" in several internal variables and internal methods. It Reduced the ambiguity between the legislation as a tax and benefit system and the legislation as the parameters.
  - `TaxBenefitSystem.compact_legislation_by_instant_cache` -> `TaxBenefitSystem._parameters_at_instant_cache`
  - `TaxBenefitSystem.get_baseline_compact_legislation()` -> `TaxBenefitSystem._get_baseline_parameters_at_instant()`
  - `Simulation.compact_legislation_by_instant_cache` -> `Simulation._parameters_at_instant_cache`
  - `Simulation.get_compact_legislation()` -> `Simulation._get_parameters_at_instant()`
  - `Simulation.get_baseline_compact_legislation()` -> `Simulation._get_baseline_parameters_at_instant()`

* The optionnal parameter `traced_simulation` is removed in function `TaxBenefitSystem.get_compact_legislation()` (now `TaxBenefitSystem.get_parameters_at_instant()`). This parameter had no effect.

* The optional parameter `with_source_file_infos` is removed in functions `TaxBenefitSystem.compute_legislation()` (now `TaxBenefitSystem._compute_parameters()`) and `TaxBenefitSystem.get_legislation()`. This parameter had no effect.

* In the API preview, update the internal transformation of the parameters.

* In the directory `script`, add a subdirectory `migrations`.

## 16.3.0

- Support `reference` attributes on all parameter XML nodes.
  - You can now add a `reference` on a `<VALUE>`, for example.

## 16.2.0

In the preview web API, for variables of type `Enum`:

* Accept and recommend to use strings as simulation inputs, instead of the enum indices.
  - For instance, `{"housing_occupancy_status": {"2017-01": "Tenant"}}` is now accepted and prefered to `{"housing_occupancy_status": {"2017-01": 0}}`).
  - Using the enum indices as inputs is _still accepted_ for backward compatibility, but _should not_ be encouraged.
* Return strings instead of enum indices.
  - For instance, is `housing_occupancy_status` is calculated for `2017-01`, `{"housing_occupancy_status": {"2017-01": "Tenant"}}` is now returned, instead of `{"housing_occupancy_status": {"2017-01": 0}}`.
* In the `/variable/<variable_name>` route, document possible values.
* In the Open API specification, document possible values following JSON schema.
* In the `/variable/<variable_name>` route:
  - Document possible values
  - Use a string as a default value (instead of the enum default indice)
* In the Open API specification, document possible values following JSON schema.

### 16.1.1

#### Minor Change

* Enhance logs
    - Replace prints by proper logs
    - Give clear and concise feedback to users when a formula cannot compute.

## 16.1.0

* Enable API monitoring with Piwik
  - See the [documentation](https://github.com/openfisca/openfisca-core/#tracker)

# 16.0.0

#### Breaking changes - [#545](https://github.com/openfisca/openfisca-core/pull/545)

* Deprecate `parsers`
  - They can no longer be installed through `pip install openfisca_core[parsers]`
  - They can still install them directly with `pip install openfisca_parsers`, but they won't be maintained.

### 15.0.1 - [#538](https://github.com/openfisca/openfisca-core/pull/538)

#### Bug fix

- Make `missing_value` base function compatible with v4 syntax and extra params

# 15.0.0

#### Breaking changes - [#525](https://github.com/openfisca/openfisca-core/pull/525)

* Rename `Variable` attribute `url` to `reference`
  - This attribute is the legislative reference of a variable.
  - As previously, this attribute can be a string, or a list of strings.
* Rename `Variable` attribute `reference` to `baseline_variable`
  - This attibute is, for a variable defined in a reform, the baseline variable the reform variable is replacing.
* Remove variable attribute `law_reference`
* Rename `TaxBenefitSystem.reference` to `TaxBenefitSystem.baseline`
* Rename `TaxBenefitSystem.get_reference_compact_legislation` to `TaxBenefitSystem.get_baseline_compact_legislation`
* Rename `Simulation.reference_compact_legislation_by_instant_cache` to `Simulation.baseline_compact_legislation_by_instant_cache`
* Rename `Simulation.get_reference_compact_legislation` to `Simulation.get_baseline_compact_legislation`
* Rename parameter `reference` of `AbstractScenario.new_simulation()` to `use_baseline`
* Rename parameter `reference` of `Simulation.legislation_at()` to `use_baseline`

### 14.1.4 - [#539](https://github.com/openfisca/openfisca-core/pull/539)

#### New features

- In the preview API `/calculate` route
  - Handle roles with no plural
  - Force all persons to be allocated to all entities
  - Improve error messages
  - Detect unexpected entity errors first
- Document new simulation and entities constructors.

### 14.1.3 - [#541](https://github.com/openfisca/openfisca-core/pull/541)

#### Minor Change

- Rewrite `/calculate` example in the Open API spec so that it works for `Openfisca-France`

### 14.1.2 - [#535](https://github.com/openfisca/openfisca-core/pull/535)

#### Bug fix

- Fix `formula.graph_parameters` and `formula.to_json`
  - Bugs were introduced in `14.0.0`

- Fix `simulation.graph`
  - A bug was introduced in `14.1.0`

### 14.1.1 - [#533](https://github.com/openfisca/openfisca-core/pull/533)

#### Bug fix

- Fix `simulation.clone` and `entity.clone` methods.
  - A bug was introduced in `14.1.0`

## 14.1.0 - [#528](https://github.com/openfisca/openfisca-core/pull/528)

#### New features

- Introduce `/calculate` route in the preview API
  - Allows to run calculations.
  - Takes a simulation `JSON` as an input, and returns a copy of the input extended with calculation results.

- Handle `500` errors in the preview API
    - In this case, the API returns a JSON with details about the error.

- Allows simulations to be built from a JSON using their constructor
  - For instance `Simulation(simulation_json = {"persons": {...}, "households": {...}}, tax_benefit_system = tax_benefit_system)`

- Allows entities to be built from a JSON using their constructor
  - For instance `Household(simulation, {"first_household": {...}})`

- Introduce `tax_benefit_system.get_variables(entity = None)`
  - Allows to get all variables contained in a tax and benefit system, with filtering by entity

#### Deprecations

- Deprecate `simulation.holder_by_name`, `simulation.get_holder`, `get_or_new_holder`
  - These functionalities are now provided by `entity.get_holder(name)`

- Deprecate constructor `Holder(simulation, column)`
  - A `Holder` should now be instanciated with `Holder(entity = entity, column = column)`

### 14.0.1 - [#527](https://github.com/openfisca/openfisca-core/pull/527)

* Improve error message and add stack trace when a module import fails

# 14.0.0 - [#522](https://github.com/openfisca/openfisca-core/pull/522)

#### Breaking changes

- In variables:
  - Merge `Variable` and `DatedVariable`.
    - `Variable` can now handle formula evolution over time.
  - Remove `start_date` attribute
  - Rename `stop_date` attribute to `end`
    - Introduce end string format `end = 'YYYY-MM-DD'`
- In formulas:
  - Merge `SimpleFormula` and `DatedFormula`.
    - `Formula` evolves over time.
  - Remove `@dated_function`
    - start definition goes to formula name: `formula_YYYY[_MM[_DD]]`
    - stop is deduced from next formula start

  Before:
  ```
  class your_variable(DatedVariable):
      # ... attributes
      start_date = datetime.date(2015, 05, 01)
      stop_date = datetime.date(2017, 05, 31)

      # openfisca chooses most restrictive start in (start_date, @dated_function start)
      @dated_function(start = date(2015, 1, 1), stop = date(2016, 12, 31))
      def function_2015_something(self, simulation, period):
          # Calculate for 2015

      @dated_function(start = date(2016, 1, 1))
      def function__different_name(self, simulation, period):
          # Calculate for 2016 > 2017-05-31 (including 2017-05-31 stop_date day)
  ```
  After:
  ```
  class your_variable(Variable):
      # ... unchanged attributes
      end = '2017-05-31'  # string format 'YYYY-MM-DD'

      # name should begin with 'formula' / you define the start in the name
      def formula_2015_05_01(self, simulation, period):  # stops on last day before next formula
          # Calculate for 2015

      def formula_2016(self, simulation, period):  # similar to formula_2016_01_01 or formula_2016_01
          # Calculate for 2016+ > 2017-05-31 (including 2017-05-31 end day)
  ```

#### New features

- Change `ETERNITY` period effect
  - Remove restriction that prevented formula changes over time for a variable with `definition_period = ETERNITY`.

### 13.0.1 - [#526](https://github.com/openfisca/openfisca-core/pull/526)

### Bug fix

* Require numpy < 1.13.
  - Openfisca is not yet compatible with the new numpy version 1.13.

# 13.0.0

#### Breaking changes

* Disallow text out of tags in XML parameters
  - This prevents to add "comments" that would be lost by automated transformation of these parameters.

#### New features

* Introduce a "reference" attribute to document a source in XML parameters

## 12.3.0

* Serve the [OpenAPI specification](https://www.openapis.org/) under the API route `/spec/`

## 12.2.0

* Use `nose` in the `openfisca-run-test` script
  - This avoids boilerplate code on country packages, and makes parallelism easier to set on Circle CI.

### 12.1.4

* Fix package naming conflict between the preview API and the official one.
* Fix import error

### 12.1.3

* Validate XML parameters with lxml and a XML Schema
* Raise nicer errors during validation

### 12.1.2

* Improve the error when the period argument is forgotten in entity call

### 12.1.1

* When replacing a variable by another one in a reform, assume the new variable has the same metadata than the reference one.
  - The is currently the behaviour for all other metadata.

## 12.1.0

* Include the preview API into OpenFisca-Core
* Remove internationalization (`i18n`, `Babel`)
* Use CircleCI instead of Travis

### 12.0.3

* Fix variable `source_file_path` computation.
  - Make sure the tax and benefit system `location` metadata is consistent with the actual python files being loaded.

### 12.0.2

* Fix a bug introduced by 11.0.0: variables with several references could not be loaded.

### 12.0.1

* Fix a bug introduced by 12.0.0: the description of a parameter node was no longer exported in the parameter JSON.

# 12.0.0

#### Breaking changes

* Deprecate and remove the `fin` attribute in XML parameters.
  - The end date of a parameter is assumed to be the start of the next one.
  - The `<END>` indicates that a parameter does not exist anymore
* Deprecate and remove the `fuzzy` attribute in XML parameters.
  - By construction, the value of a parameter is always extended towards the future.
  - To indicate a likely change of the legislation, a `<PLACEHOLDER>` can be added.
* Deprecate and remove `reforms.create_item`
  - New items are created directly with the method `reforms.update_items`.
* Deprecate and remove `reforms.split_item_containing_instant`
  - Splitting items does not make sense in the new convention. Use `reform.update_items` to update the parameters.

# 11.0.0

#### Breaking changes

These breaking changes only concern variable and tax and benefit system **metadata**. They **do not** impact calculations.

* Make `tax_benefit_system.get_package_metadata()` return a `dict` instead of a `tuple`
* Make `column.source_file_path` a relative path (was absolute before)
* Make `column.url` a list instead of a string

#### New features

* Make `tax_benefit_system.get_package_metadata()` more robust
  - Handle reforms
  - Handle tax and benefit systems that are not defined within a package and/or a distribution

#### Technical changes

* Turn `Variable`s with a `start_date` and/or a `stop_date` into `DatedVariable`s
  - This is transparent for users.

### 10.0.2

* Do not cache values for neutralized variables
  - To reduce memory usage for large population simulations

### 10.0.1

* Improve the raised error message when a wrong period type is given as an input

# 10.0.0

#### Breaking changes

* In YAML tests:
  - Deprecate and remove the `IGNORE_` prefix
  - Deprecate and remove the `ignore` property
* In the YAML test runner:
  - Deprecate and remove the `force` option (`-f` in the shell script)
  - Deprecate and remove the `default_absolute_error_margin` option (`-M` in the shell script)
  - Deprecate and remove the `default_relative_error_margin` option (`-m` in the shell script)

#### New features

* Add `Reform` and `numpy.round` (as `round_`) in the model API
* Introduce `tax_benefit_system.apply_reform(reform_path)`
* Allow YAML tests to declare the reforms they need to be executed (through the `reforms` property)

#### Technical changes

* Move the `dummy_extension` to `OpenFisca-Dummy-Country`
* Test `openfisca-run-test` script

## 9.1.0

* Rename `neutralize_column` to `neutralize_variable`
  - Deprecate `neutralize_column` without removing it
* Document `neutralize_variable`

### 9.0.2

* Fix spelling in error messages

### 9.0.1

* Test marginal scales
* Move tests out of the main package
* These changes are transparent for users

# 9.0.0

* Make sure identic periods are stringified the same way
* _Breaking changes_:
  - Change `periods.period` signature.
    - It now only accepts strings.
  - Restrict the possible inputs for `periods.period`
    - The authorized formats are listed in [the doc](http://openfisca.org/doc/periodsinstants.html)
  - Deprecate and remove:
    - `periods.json_or_python_to_period`
    - `periods.make_json_or_python_to_period`

### 8.0.1

* Move the dummy country to [its own repository](https://github.com/openfisca/openfisca-dummy-country)

# 8.0.0

* Raise more explicit error when an invalid test case is given
* Raise more friendly error when trying to calculate a variable which doesn't exist
* _Breaking change_: Python exceptions will now be raised when the test case in invalid. Before, only a byriani error was returned. Reusers must therefore adapt their exception handling.

## 7.1.0

* Add `Entity.to_json` method. Used by OpenFisca-Web-API in `/entity` endpoint in particular.

### 7.0.1

* Declare `Openfisca-Parsers` as an optional dependency of `Openfisca-Core`.

# 7.0.0

* Make it mandatory to provide a period when calculating a variable.
  - When a computation is requested (with *.calculate_output, entities.__call__, *.calculate[_add|_divide], *.compute[_add|_divide]), the argument `period` is no longer optional.
  - Previously, the period of the simulation was used instead of a missing period. It was error-prone, as values would be returned for the wrong period, without any error or warning to alert the formula writer about a likely coding error.

## 6.1.0

* Move `base.py` content (file usually located in country packages) to core module `formula_toolbox` so that it can be reused by all countries
* Use `AbstractScenario` if no custom scenario is defined for a tax and benefit sytem

# 6.0.0

#### Breaking changes

* Add **mandatory** attribute `definition_period` to variables
* Enforce that inputs provided for a variable match the variable `definition_period`
  - If a `set_input` attribute has been defined, automatically cast the input accordingly.
* Change the expected output of a formula
  - Only `result` must be returned, instead of `period, result`
* Deprecate and remove:
  - `simulation.print_trace`
  - `simulation.calculate_add_divide` and `simulation.compute_add_divide`
  - `last_duration_last_value` base function
  - `variables_name_to_skip` and `use_set_input_hooks` parameters in `scenario.fill_simulation`
  - `holders.new_test_case_array`
* Deprecate and forbid `dated_holder.array = ...`
* Raise an error when inconsistent year and month inputs provided for a variable
  - Before, the year value would be silently ignored.
* Rename `period.this_month` to `period.first_month`

#### Technical changes

* Make sure the cache only store values for periods matching the variable `definition_period`
* Use a cache buffer in simulation initialisation when axes are used, to avoid `set_input` conflicts
* Make `DatedHolder` only a wrapper of a variable value for a given period, and no more a dated view of a `Holder`

#### Documentation

* the attribute `definition_period` is documented here : http://openfisca.org/doc/coding-the-legislation/35_periods.html

### 5.0.2

* Add `TaxBenefitSystem` doc to the reference doc
  - This is transparent for all users

### 5.0.1

* Improve `openfisca-run-test` script
  - Make country package detection more robust (it only worked for packages installed in editable mode)
  - Use spaces instead of commas as separator in the script arguments when loading several extensions or reforms (this is more standard)
* Refactor the `scripts` module to seperate the logic specific to yaml test running from the one that can be re-used by any script which needs to build a tax and benefit system.

# 5.0.0

* Move `json_or_python_to_test_case` from country packages to core
* Breaking change: `scenarios.set_entities_json_id` has been moved, and should not be considered a public function.

### 4.3.6

* Bug fix : handle the case when CompactNode.name is None.

### 4.3.5

* Refactor decomposition TaxBenefitSystem attributes. Reform inherit the decomposition_file_path from the reference TaxBenefitSystem.
  This does not require changing anything from the caller, which should use the `decompositions.get_decomposition_json` function instead of those attributes.

### 4.3.4

* Fix occasionnal `NaN` creation in `MarginalRateTaxScale.calc` resulting from `0 * np.inf`

### 4.3.3

* Use the actual TaxBenefitSystem and not its reference when neutralizing a column.

### 4.3.2

* Fix `to_value_json` for `DatedVariable` with extra parameters.

This was causing a crash when calculating intermediate variables with the API.

Unlike simple formulas, a `DatedVariable` have several functions. We thus need to select the right one according to the period before doing parameters introspection.

### 4.3.1

* Fix `set_input` and `default` setting in `new_filled_column`

## 4.3.0

* Add reference documentation

### 4.2.1

* Fix permanent and period size independent variables neutralization

## 4.2.0

* Introduce a YAML test runner in openfisca_core
  - Introduce command line tool `openfisca-run-test`

* Refactor the dummy tax benefit system included in openfisca-core
  - Make the dummy country look like a real one
  - Split defining the country from testing

### 4.1.7

* Improve docstring of `MarginalTaxRate.inverse` and add test

### 4.1.6

* Decrease verbosity of `combine_tax_scales`

### 4.1.5

* Enable `extra_params` in formulas with new syntax.

### 4.1.4-Beta

* Fixup 4.1.2:
  * When building positions, handle cases where persons belonging to an entity are not grouped by entity in the persons array.

### 4.1.3-Beta

* Fix bug in entity.sum

### 4.1.2-Beta

* Enable simulation initialization with only legacy roles
  * New roles are in this case automatically infered
  * Positions are always infered from persons entity id

### 4.1.1-Beta

* Fix update_legislation in reforms

### 4.1.0-Beta

* Add `conflicts` and `origin` fields to xml params (needed for baremes IPP importation)

### 4.0.0-Beta

  * Refactor formula syntax

    - Don't use the object simulation in formula writing. The entity the variable is calculated for is now the first argument of the formula, for instance `person` or `family`.

    - The `legislation` is now the (optional) third argument of a formula. It is a function that can be called with a period (or an instant) for argument, and will compute the legislation at `period.start`.

    -  Don't use `calculate_add` and equivalents. Instead, `add` and `divide` are just given in the `options` argument, for instance `options = [ADD]`.

    - Rename `entity_class` to `entity`.

    - Don't explicitly use a `calculate` method, but the `person('salary', period)` notation instead.

  * Introduce implicit conversions between entities, and improve aggregations formulas.

  * Deprecate PersonToEntityColumn and EntityToPersonColumn

  * Change the way entities are declared

  More information on https://github.com/openfisca/openfisca-core/pull/415

## 3.1.0

* Add a `DeprecationWarning` when using a `DateCol` with no `default`, but keep the default date to 1970-01-01.
* Enforce `DateCol.default` to be a `date`.

### 3.0.3

* Fix `cerfa_field` validation in `Column`, `Formula` and `AbstractConversionVariable`.
  Previously, some variables having `cerfa_field` as a `dict` were converted to `unicode` by mistake.
  See https://github.com/openfisca/openfisca-france/issues/543

### 3.0.2

* Move `calmar.py` to [OpenFisca-Survey-Manager](https://github.com/openfisca/openfisca-survey-manager).

  No incidence on users since it was only needed for dataframes.

### 3.0.1

* Adapt requested_period_last_value and last_duration_last_value to extra params

# 3.0.0

* Update introspection data. This allows to enhance data served by the web API which itself feeds the Legislation Explorer.

### 2.2.2

* Update travis procedures

### 2.2.1

* Remove conda from travis config

## 2.2.0

* Implement simulation.calculate `print_trace=True` argument. Options: `max_depth` and `show_default_values`

  Examples:
  ```python
  simulation = scenario.new_simulation(trace=True)
  simulation.calculate('irpp', 2014, print_trace=True)
  simulation.calculate('irpp', 2014, print_trace=True, max_depth=-1)
  simulation.calculate('irpp', 2014, print_trace=True, max_depth=-1, show_default_values=False)
  ```

## 2.1.0 – [diff](https://github.com/openfisca/openfisca-core/compare/2.0.3...2.0.4)

* Load extensions from pip packages

### 2.0.4 – [diff](https://github.com/openfisca/openfisca-core/compare/2.0.3...2.0.4)

* Use DEFAULT_DECOMP_FILE attribute from reference TB system

### 2.0.3 – [diff](https://github.com/openfisca/openfisca-core/compare/2.0.2...2.0.3)

* Explicit the error when a variable is not found

### 2.0.2 – [diff](https://github.com/openfisca/openfisca-core/compare/2.0.1...2.0.2)

* Update numpy dependency to 1.11

### 2.0.1 – [diff](https://github.com/openfisca/openfisca-core/compare/2.0.0...2.0.1)

* Force updating version number and CHANGELOG.md before merging on master
* Release tag and Pip version automatically

# 2.0.0 – [diff](https://github.com/openfisca/openfisca-core/compare/1.1.0...2.0.0)

* Variables are not added to the TaxBenefitSystem when the entities class are imported, but explicitely when the TaxBenefitSystem is instanciated.
  * Metaclasses are not used anymore.
* New API for TaxBenefitSystem
  * Columns are now stored in the TaxBenefitSystem, not in entities.
* New API for rerforms.
* XmlBasedTaxBenefitSystem is deprecated, and MultipleXmlBasedTaxBenefitSystem renamed to TaxBenefitSystem

## 1.1.0 – [diff](https://github.com/openfisca/openfisca-core/compare/1.0.0...1.1.0)

* Implement cache opt out system

# 1.0.0 – [diff](https://github.com/openfisca/openfisca-core/compare/0.5.4...1.0.0)

* Remove `build_column` obsolete function. Use `Variable` class instead.

## 0.5.4 – [diff](https://github.com/openfisca/openfisca-core/compare/0.5.3...0.5.4)

* Merge pull request #382 from openfisca/fix-sum-by-entity
* The result size must be the targent entity'one

## 0.5.3 – [diff](https://github.com/openfisca/openfisca-core/compare/0.5.2...0.5.3)

* Many updates

## 0.5.2 – [diff](https://github.com/openfisca/openfisca-core/compare/0.5.1...0.5.2)

* Add trim option to marginal rate computation
* Compute stop date of whole tax scale instead of a single bracket.
* Use bracket stop date instead of legislation stop date inside a bracket.
* Introduce reference periods
* Fix roles_count bug : was set to 1 for scenarios vectorially defined

## 0.5.1 – [diff](https://github.com/openfisca/openfisca-core/compare/0.5.0...0.5.1)

* Move docs to gitbook repo
* Upgrade to new Travis infrastructure
* Enhance errors display when a reform modifies the legislation

## 0.5.0

* First release uploaded to PyPI
