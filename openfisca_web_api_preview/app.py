# -*- coding: utf-8 -*-

import os
from flask import Flask, jsonify, abort, request, make_response
from flask_cors import CORS
import dpath


from openfisca_core.simulations import Simulation, SituationParsingError
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

    @app.route('/')
    def welcome():
        return "Welcome to the OpenFisca Web API"

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

    def handle_invalid_json(error):
        json_response = jsonify({
            'error': 'Invalid JSON: {}'.format(error.message),
            })

        abort(make_response(json_response, 400))

    @app.route('/calculate', methods=['GET'])
    def welcome_calculate():
        return "Welcome to the Calculate endpoint of the OpenFisca Web API"

    @app.route('/calculate', methods=['POST'])
    def calculate():
        request.on_json_loading_failed = handle_invalid_json
        input_data = request.get_json()
        try:
            simulation = Simulation(tax_benefit_system = data['tax_benefit_system'], simulation_json = input_data)
        except SituationParsingError as e:
            abort(make_response(jsonify(e.error), e.code or 400))

        requested_computations = dpath.util.search(input_data, '*/*/*/*', afilter = lambda t: t is None, yielded = True)

        for computation in requested_computations:
            path = computation[0]
            entity_plural, entity_id, variable_name, period = path.split('/')
            result = simulation.calculate(variable_name, period).tolist()
            entity = simulation.get_entity(plural = entity_plural)
            entity_index = entity.ids.index(entity_id)
            entity_result = result[entity_index]

            dpath.util.set(input_data, path, entity_result)

        return jsonify(input_data)

    @app.after_request
    def apply_headers(response):
        response.headers.extend({
            'Country-Package': data['country_package_metadata']['name'],
            'Country-Package-Version': data['country_package_metadata']['version']
            })
        return response

    @app.errorhandler(500)
    def internal_server_error(e):
        response = jsonify({"error": "Internal server error: " + e.message})
        response.status_code = 500
        return response

    return app
