=============
``/variable``
=============

.. http:get:: /variable/<variable_id>

    Get data about the ``<variable_id>`` variable

    :>json String defaultValue: Variable default value.
    :>json String definitionPeriod: Definition period of the variable. Possible values : ``YEAR``, ``MONTH``, ``ETERNITY``.
    :>json String description: Variable description.
    :>json String entity: Entity for which the variable is defined. For instance, ``person``, ``household``…
    :>json Object formulas: History of formulas used to compute the variable. If no start date has been specified for the formula, ``0001-01-01`` is used by convention. If one of the property value of this object is ``null``,  the variable doesn't have any formula from the date encoded in the corresponding key.
    :>json String id: Variable id.
    :>json Array references: Legislative references of the variable.
    :>json String source: Link towards the variable code on GitHub.
    :>json String valueType: The type of the variable.
    :reqheader Country-Package: The name of the country package served by the API
    :resheader Country-Package-Version: The version of the country package served by the API
    :statuscode 200: The requested variable description is sent back in the response body.
    :statuscode 404: the variable ``<variable_id>`` doesn't exist.

    **Example request**:

    .. sourcecode:: http

        GET /variable/income_tax HTTP/1.1

    **Example response**:

    .. sourcecode:: http

        HTTP/1.1 200 OK
        Country-Package: openfisca-france
        Country-Package-Version: 18.2.1
        Content-Type: application/json

        {
          "defaultValue": 0,
          "definitionPeriod": "MONTH",
          "description": "Basic income provided to adults",
          "entity": "person",
          "formulas": {
            "2015-12-01": {
              "content": "def function_until_2016_12(person, period, legislation):\n    age_condition = person('age', period) >= legislation(period).general.age_of_majority\n    salary_condition = person('salary', period) == 0\n    return age_condition * salary_condition * legislation(period).benefits.basic_income  # The '*' is also used as a vectorial 'and'. See https://doc.openfisca.fr/coding-the-legislation/25_vectorial_computing.html#forbidden-operations-and-alternatives\n",
              "source": "https://github.com/openfisca/openfisca-country-template/blob/1.0.0.dev0/openfisca_country_template/variables/benefits.py#L29-L32"
            },
            "2016-12-01": {
              "content": "def function_from_2016_12(person, period, legislation):\n    age_condition = person('age', period) >= legislation(period).general.age_of_majority\n    return age_condition * legislation(period).benefits.basic_income  # This '*' is a vectorial 'if'. See https://doc.openfisca.fr/coding-the-legislation/30_case_disjunction.html#simple-multiplication\n",
              "source": "https://github.com/openfisca/openfisca-country-template/blob/1.0.0.dev0/openfisca_country_template/variables/benefits.py#L22-L24"
            }
          },
          "id": "basic_income",
          "references": [
            "https://law.gov.example/basic_income"
          ],
          "source": "https://github.com/openfisca/openfisca-country-template/blob/1.0.0.dev0/openfisca_country_template/variables/benefits.py#L13-L32",
          "valueType": "Float"
        }
