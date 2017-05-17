==============
``/variables``
==============

.. http:get:: /variables

    All the variables contained in the tax and benefit system

    :resheader Country-Package: The name of the country package served by the API
    :resheader Country-Package-Version: The version of the country package served by the API
    :statuscode 200: no error

    **Example request**:

    .. sourcecode:: http

        GET /variables HTTP/1.1

    **Example response**:

    .. sourcecode:: http

        HTTP/1.1 200 OK
        Country-Package: openfisca-france
        Country-Package-Version: 18.2.1
        Content-Type: application/json

        {
          "age": {
            "description": "Person's age"
          },
          "basic_income": {
            "description": "Basic income provided to adults"
          },
          "birth": {
            "description": "Birth date"
          },
          "disposable_income": {
            "description": "Actual amount available to the person at the end of the month"
          },
          "income_tax": {
            "description": "Income tax"
          },
          "salary": {
            "description": "Salary"
          },
        }
