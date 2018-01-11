# -*- coding: utf-8 -*-

import os
from os import linesep
from flask import Flask, jsonify, abort, request, make_response
from werkzeug.contrib.fixers import ProxyFix
from flask_cors import CORS
import dpath

from openfisca_core.simulations import Simulation, SituationParsingError
from openfisca_core.indexed_enums import Enum
from loader import build_data
import traceback
import logging


log = logging.getLogger('gunicorn.error')


def init_tracker(url, idsite, tracker_token):
    try:
        from openfisca_tracker.piwik import PiwikTracker
        tracker = PiwikTracker(url, idsite, tracker_token)

        info = linesep.join([u'You chose to activate the `tracker` module. ',
                             u'Tracking data will be sent to: ' + url,
                             u'For more information, see <https://github.com/openfisca/openfisca-core#tracker-configuration>.'])
        log.info(info)
        return tracker

    except ImportError:
        message = linesep.join([traceback.format_exc(),
                                u'You chose to activate the `tracker` module, but it is not installed.',
                                u'For more information, see <https://github.com/openfisca/openfisca-core#tracker-installation>.'])
        log.warn(message)


def create_app(tax_benefit_system,
               tracker_url = None,
               tracker_idsite = None,
               tracker_token = None
               ):

    if not tracker_url or not tracker_idsite:
        tracker = None
    else:
        tracker = init_tracker(tracker_url, tracker_idsite, tracker_token)

    app = Flask(__name__)
    app.wsgi_app = ProxyFix(app.wsgi_app, num_proxies = 1)  # Fix request.remote_addr to get the real client IP address
    CORS(app, origins = '*')

    app.url_map.strict_slashes = False  # Accept url like /parameters/

    data = build_data(tax_benefit_system)

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

    @app.route('/calculate', methods=['POST'])
    def calculate():
        tax_benefit_system = data['tax_benefit_system']
        request.on_json_loading_failed = handle_invalid_json
        input_data = request.get_json()
        try:
            simulation = Simulation(tax_benefit_system = tax_benefit_system, simulation_json = input_data)
        except SituationParsingError as e:
            abort(make_response(jsonify(e.error), e.code or 400))

        requested_computations = dpath.util.search(input_data, '*/*/*/*', afilter = lambda t: t is None, yielded = True)

        for computation in requested_computations:
            path = computation[0]
            entity_plural, entity_id, variable_name, period = path.split('/')
            variable = tax_benefit_system.get_variable(variable_name)
            result = simulation.calculate(variable_name, period)
            entity = simulation.get_entity(plural = entity_plural)
            entity_index = entity.ids.index(entity_id)

            if variable.value_type == Enum:
                entity_result = result.decode()[entity_index].name
            else:
                entity_result = result.tolist()[entity_index]

            dpath.util.set(input_data, path, entity_result)

        return jsonify(input_data)

    @app.route('/trace', methods=['POST'])
    def trace():
        tax_benefit_system = data['tax_benefit_system']
        request.on_json_loading_failed = handle_invalid_json
        input_data = request.get_json()
        try:
            simulation = Simulation(tax_benefit_system = tax_benefit_system, simulation_json = input_data, trace = True)
        except SituationParsingError as e:
            abort(make_response(jsonify(e.error), e.code or 400))

        requested_computations = dpath.util.search(input_data, '*/*/*/*', afilter = lambda t: t is None, yielded = True)
        for computation in requested_computations:
            path = computation[0]
            entity_plural, entity_id, variable_name, period = path.split('/')
            simulation.calculate(variable_name, period).tolist()

        return jsonify({
            "trace": simulation.tracer.trace,
            "entitiesDescription": {entity.plural: entity.ids for entity in simulation.entities.itervalues()},
            "requestedCalculations": list(simulation.tracer.requested_calculations)
            })

    @app.after_request
    def apply_headers(response):
        response.headers.extend({
            'Country-Package': data['country_package_metadata']['name'],
            'Country-Package-Version': data['country_package_metadata']['version']
            })
        return response

    @app.after_request
    def track_requests(response):
        if tracker:
            if request.headers.get('dnt'):
                tracker.track(request.url)
            else:
                tracker.track(request.url, request.remote_addr)
        return response

    @app.errorhandler(500)
    def internal_server_error(e):
        response = jsonify({"error": "Internal server error: " + e.message.strip(os.linesep).replace(os.linesep, ' ')})
        response.status_code = 500
        return response

    return app
