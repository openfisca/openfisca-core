=============
``/parameter``
=============

.. http:get:: /parameter/<parameter_id>

    Get data about the ``<parameter_id>`` parameter

    :>json description: Parameter description.
    :>json id: Parameter id.
    :>json values: Parameter values history. Only present if the parameter is a simple one. A ``null`` value means that the parameter does not exist anymore.
    :>json brackets: Marginal scale history. Only present if the parameter is a marginal scale. A ``null`` value means that the scale does not exist anymore.
    :resheader Country-Package: The name of the country package served by the API.
    :resheader Country-Package-Version: The version of the country package served by the API.
    :statuscode 200: no error.
    :statuscode 404: the parameter ``<parameter_id>`` doesn't exist.

    **Example: Simple parameter**

        **Request**

            .. sourcecode:: http

                GET /parameter/taxes.income_tax_rate HTTP/1.1

        **Response**:

            .. sourcecode:: http

                HTTP/1.1 200 OK
                Country-Package: openfisca-france
                Country-Package-Version: 18.2.1
                Content-Type: application/json

                {
                  "description": "Income tax rate",
                  "id": "taxes.income_tax_rate",
                  "values": {
                    "2012-01-01": 0.16,
                    "2013-01-01": 0.13,
                    "2014-01-01": 0.14,
                    "2015-01-01": 0.15
                  }
                }

    **Example: Marginal scale**

        **Request**

            .. sourcecode:: http

                GET /parameter/taxes.social_security_contribution HTTP/1.1

        **Response**:

            .. sourcecode:: http

                HTTP/1.1 200 OK
                Country-Package: openfisca-france
                Country-Package-Version: 18.2.1
                Content-Type: application/json

                {
                  "brackets": {
                    "2013-01-01": {
                      "0.0": 0.03,
                      "12000.0": 0.1
                    },
                    "2014-01-01": {
                      "0.0": 0.03,
                      "12100.0": 0.1
                    },
                    "2015-01-01": {
                      "0.0": 0.04,
                      "12200.0": 0.12
                    },
                    "2016-01-01": {
                      "0.0": 0.04,
                      "12300.0": 0.12
                    },
                    "2017-01-01": {
                      "0.0": 0.02,
                      "6000.0": 0.06,
                      "12400.0": 0.12
                    }
                  },
                  "description": "Social security contribution tax scale",
                  "id": "taxes.social_security_contribution"
                }

