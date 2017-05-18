==============
``/parameters``
==============

.. http:get:: /parameters

    Get the parameters contained in the tax and benefit system.

    The response is formatted as an object whose keys are the parameters id and values objects with a single property, description.

    :resheader Country-Package: The name of the country package served by the API
    :resheader Country-Package-Version: The version of the country package served by the API
    :statuscode 200: The list of all parameters is sent back in the response body.

    **Example request**:

    .. sourcecode:: http

        GET /parameters HTTP/1.1

    **Example response**:

    .. sourcecode:: http

        HTTP/1.1 200 OK
        Country-Package: openfisca-france
        Country-Package-Version: 18.2.1
        Content-Type: application/json

        {
          "benefits.basic_income": {
            "description": "Amount of the basic income"
          },
          "benefits.housing_allowance": {
            "description": "Housing allowance amount (as a fraction of the rent)"
          },
          "general.age_of_majority": {
            "description": "Age of majority"
          },
          "taxes.income_tax_rate": {
            "description": "Income tax rate"
          },
          "taxes.social_security_contribution": {
            "description": "Social security contribution tax scale"
          }
        }
