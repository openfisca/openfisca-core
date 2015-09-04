# OpenFisca reforms

> This documentation explains how to write a reform.
> To know how to declare an existing reform to an instance of the OpenFisca Web API that you host, please read
> [OpenFisca-Web-API reforms](https://github.com/openfisca/openfisca-web-api/tree/next/docs/reforms.md)

## Just show me the code! [tl;dr](https://fr.wiktionary.org/wiki/tl;dr)

Examples can be found in [OpenFisca-France bundled reforms](https://github.com/openfisca/openfisca-france/tree/next/openfisca_france/reforms), for example [Trannoy-Wasmer reform](https://github.com/openfisca/openfisca-france/blob/next/openfisca_france/reforms/trannoy_wasmer.py).

Some reforms exist as separate git repository, for example [Landais Piketty Saez ](https://github.com/openfisca/openfisca-france-reform-landais-piketty-saez).

## What is a reform?

In OpenFisca a reform is an extension of the tax and benefit system.

The tax and benefit system of the country knows about the laws that are already adopted, were existing in the past, or will exist in a near future. In contrast, the reforms are propositions that people do but are not officially voted.

Reforms can add, change or remove simulation variables, either input variables or computed variables with formulas.
They can change the legislation of the tax and benefit system too.

Reforms can be chained as they take a reference tax and benefit system in parameter.

## How to write a reform?

[OpenFisca-Core](https://github.com/openfisca/openfisca-core) provides a `TaxBenefitSystem` class to represent a tax and benefit system. It provides too a `Reform` class which inherits `TaxBenefitSystem`.

To write a reform which will work with [OpenFisca-Web-API](https://github.com/openfisca/openfisca-web-api),
you have to implement a `build_reform` function which returns an instance of the `Reform` class.

The `reforms.make_reform` function does the job.

Here is how to do a reform which does nothing, for the purpose of the example:

```
def build_reform(tax_benefit_system):
    Reform = reforms.make_reform(
        key = 'empty',
        name = u'Dummy empty reform',
        reference = tax_benefit_system,
        )
    reform = Reform()
    return reform
```

> `reforms.make_reform` returns a `Reform` class that you can instantiate in `build_reform`.
> You can modify this instance if needed, then return it.

The `Reform` class provides a decorator to declare formulas (`@Reform.formula`) and another one to declare input variables (`@Reform.input_variable`).

The reference `tax_benefit_system` won't be touched.

Here is an example:

```
def build_reform(tax_benefit_system):
    Reform = reforms.make_reform(
        key = 'change_formula',
        name = u'Dummy reform with changed formula',
        reference = tax_benefit_system,
        )

    @Reform.formula
    class charges_deduc(formulas.SimpleFormulaColumn):
        label = u"Charge déductibles always returning 999"
        reference = charges_deductibles.charges_deduc
        def function(self, simulation, period):
            return period, 999

    reform = Reform()
    return reform
```

To change the JSON data structure of the legislation in the reform, you call the `reform.modify_legislation_json` method which takes as a parameter a callback.
This callback is a function you write in which the legislation JSON will be modified.
It takes in parameter a copy of the legislation_json of the reference tax and benefit system that you can modify (do not handle the copy yourself) and return.

> This mechanism allows some optimisations: the deepcopy of the legislation_json occurs only once.

Here is an example:

```
def modify_legislation_json(reference_legislation_json_copy):
    reference_legislation_json_copy['children']['xxx']['values'][0]['value'] = 0
    return reference_legislation_json_copy


def build_reform(tax_benefit_system):
    Reform = reforms.make_reform(
        key = 'new_legislation',
        name = u'Dummy reform with new legislation',
        reference = tax_benefit_system,
        )

    reform = Reform()
    reform.modify_legislation_json(modifier_function = modify_legislation_json)
    return reform
```

> You have to know about the structure of the legislation JSON data structure to modify it.

For more details see the examples linked in the tl;dr section above.

## Use from the Web API

Please read the dedicated documentation:
[OpenFisca-Web-API reforms](https://github.com/openfisca/openfisca-web-api/tree/next/docs/reforms.md)
