# -*- coding: utf-8 -*-

import os
from flask import Flask, jsonify, abort
from flask_cors import CORS

from loader import build_data


def create_app(country_package = os.environ.get('COUNTRY_PACKAGE')):
    if country_package is None:
        raise ValueError(
            u"You must specify a country package to start the API. "
            u"For instance, `COUNTRY_PACKAGE=openfisca_france flask run`"
            .encode('utf-8')
            )

    app = Flask(__name__)
    CORS(app, origins = '*')

    app.url_map.strict_slashes = False  # Accept url like /parameters/

    data = build_data(country_package)

    @app.route('/parameters')
    def get_parameters():
        return jsonify(data['parameters_description'])

    @app.route('/parameter/<id>')
    def get_parameter(id):
        parameter = data['parameters'].get(id)
        if parameter is None:
            raise abort(404)
        return jsonify(parameter)

    @app.route('/variables')
    def get_variables():
        return jsonify(data['variables_description'])

    @app.route('/variable/<id>')
    def get_variable(id):
        variable = data['variables'].get(id)
        if variable is None:
            raise abort(404)
        return jsonify(variable)

    @app.route('/spec')
    def get_spec():
        return jsonify(data['openAPI_spec'])

    @app.after_request
    def apply_headers(response):
        response.headers.extend({
            'Country-Package': data['country_package_metadata']['name'],
            'Country-Package-Version': data['country_package_metadata']['version']
            })
        return response

    return app
