# -*- coding: utf-8 -*-

import os
from flask import Flask, jsonify, abort, request, make_response
from flask_cors import CORS
import dpath


from openfisca_core.simulations import Simulation, SituationParsingError
from loader import build_data
from errors import handle_invalid_json


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

    @app.route('/calculate', methods=['POST'])
    def calculate():
        request.on_json_loading_failed = handle_invalid_json
        input_data = request.get_json()
        try:
            simulation = Simulation(tax_benefit_system = data['tax_benefit_system'], simulation_json = input_data)
        except SituationParsingError as e:
            abort(make_response(jsonify(e.error), e.code or 400))

        requested_computations = dpath.util.search(input_data, '**', afilter = lambda t: t is None, yielded = True)

        for computation in requested_computations :
            full_path = computation[0]
            path = full_path.split('/')
            result = simulation.calculate(path[-2], path[-1]).tolist()
            entity = [entity for entity in simulation.entities.values() if entity.plural == path[0]][0]
            entity_index = entity.ids.index(path[1])
            entity_result = result[entity_index]

            dpath.util.set(input_data, full_path, entity_result)


        return jsonify(input_data)

    @app.after_request
    def apply_headers(response):
        response.headers.extend({
            'Country-Package': data['country_package_metadata']['name'],
            'Country-Package-Version': data['country_package_metadata']['version']
            })
        return response

    return app
