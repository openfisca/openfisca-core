# Parameters

The `policyengine_core.parameters` module contains the classes that define how parameters function. This mainly revolves around the 'at-instant' pattern: parameters are defined as a function of time, and are evaluated at a given instant.

## Parameter

```{eval-rst}
.. autoclass:: policyengine_core.parameters.parameter.Parameter
    :members:
    :undoc-members:
    :show-inheritance:
```

## ParameterNode

```{eval-rst}
.. autoclass:: policyengine_core.parameters.parameter_node.ParameterNode
    :members:
    :undoc-members:
    :show-inheritance:
```

## ParameterNodeMetadata

```{eval-rst}
.. autoclass:: policyengine_core.parameters.parameter_node.ParameterNodeMetadata
    :members:
    :undoc-members:
    :show-inheritance:
```

## ParameterAtInstant

```{eval-rst}
.. autoclass:: policyengine_core.parameters.parameter_at_instant.ParameterAtInstant
    :members:
    :undoc-members:
    :show-inheritance:
```

## ParameterNodeAtInstant

```{eval-rst}
.. autoclass:: policyengine_core.parameters.parameter_node_at_instant.ParameterNodeAtInstant
    :members:
    :undoc-members:
    :show-inheritance:
```

## ParameterScale

```{eval-rst}
.. autoclass:: policyengine_core.parameters.parameter_scale.ParameterScale
    :members:
    :undoc-members:
    :show-inheritance:
```

## ParameterScaleBracket

```{eval-rst}
.. autoclass:: policyengine_core.parameters.parameter_scale_bracket.ParameterScaleBracket
    :members:
    :undoc-members:
    :show-inheritance:
```

## AtInstantLike

```{eval-rst}
.. autoclass:: policyengine_core.parameters.at_instant_like.AtInstantLike
    :members:
    :undoc-members:
    :show-inheritance:
```

## VectorialParameterNodeAtInstant

```{eval-rst}
.. autoclass:: policyengine_core.parameters.vectorial_parameter_node_at_instant.VectorialParameterNodeAtInstant
    :members:
    :undoc-members:
    :show-inheritance:
```

## contains_nan

```{eval-rst}
.. autofunction:: policyengine_core.parameters.helpers.contains_nan
```

## load_parameter_file

```{eval-rst}
.. autofunction:: policyengine_core.parameters.helpers.load_parameter_file
```
