# -*- coding: utf-8 -*-

from __future__ import unicode_literals, print_function, division, absolute_import
from copy import deepcopy
import logging
import os
import traceback

import dpath

from openfisca_core.simulations import Simulation, SituationParsingError
from openfisca_core.commons import to_unicode
from openfisca_core.indexed_enums import Enum
from openfisca_web_api.loader import build_data
from openfisca_web_api.errors import handle_import_error

try:
    from flask import Flask, jsonify, abort, request, make_response
    from flask_cors import CORS
    from werkzeug.contrib.fixers import ProxyFix
except ImportError as error:
    handle_import_error(error)

log = logging.getLogger('gunicorn.error')


def init_tracker(url, idsite, tracker_token):
    try:
        from openfisca_tracker.piwik import PiwikTracker
        tracker = PiwikTracker(url, idsite, tracker_token)

        info = os.linesep.join(['You chose to activate the `tracker` module. ',
                             'Tracking data will be sent to: ' + url,
                             'For more information, see <https://github.com/openfisca/openfisca-core#tracker-configuration>.'])
        log.info(info)
        return tracker

    except ImportError:
        message = os.linesep.join([traceback.format_exc(),
                                'You chose to activate the `tracker` module, but it is not installed.',
                                'For more information, see <https://github.com/openfisca/openfisca-core#tracker-installation>.'])
        log.warn(message)


def create_app(tax_benefit_system,
               tracker_url = None,
               tracker_idsite = None,
               tracker_token = None,
               welcome_message = None,
               ):

    if not tracker_url or not tracker_idsite:
        tracker = None
    else:
        tracker = init_tracker(tracker_url, tracker_idsite, tracker_token)

    app = Flask(__name__)
    app.wsgi_app = ProxyFix(app.wsgi_app, num_proxies = 1)  # Fix request.remote_addr to get the real client IP address
    CORS(app, origins = '*')

    app.config['JSON_AS_ASCII'] = False  # When False, lets jsonify encode to utf-8
    app.url_map.strict_slashes = False  # Accept url like /parameters/

    data = build_data(tax_benefit_system)

    DEFAULT_WELCOME_MESSAGE = "This is the root of an OpenFisca Web API. To learn how to use it, check the general documentation (https://openfisca.org/doc/api) and the OpenAPI specification of this instance ({}spec)."

    @app.route('/')
    def get_root():
        return jsonify({
            'welcome': welcome_message or DEFAULT_WELCOME_MESSAGE.format(request.host_url)
            }), 300

    @app.route('/parameters')
    def get_parameters():
        parameters = {
            parameter['id']: {
                'description': parameter['description'],
                'href': '{}parameter/{}'.format(request.host_url, name)
                }
            for name, parameter in data['parameters'].items()
            if parameter.get('subparams') is None  # For now and for backward compat, don't show nodes in overview
            }

        return jsonify(parameters)

    @app.route('/parameter/<path:parameter_id>')
    def get_parameter(parameter_id):
        parameter = data['parameters'].get(parameter_id)
        if parameter is None:
            # Try legacy route
            parameter_new_id = parameter_id.replace('.', '/')
            parameter = data['parameters'].get(parameter_new_id)
        if parameter is None:
            raise abort(404)
        return jsonify(parameter)

    @app.route('/variables')
    def get_variables():
        variables = {
            name: {
                'description': variable['description'],
                'href': '{}variable/{}'.format(request.host_url, name)
                }
            for name, variable in data['variables'].items()
            }
        return jsonify(variables)

    @app.route('/variable/<id>')
    def get_variable(id):
        variable = data['variables'].get(id)
        if variable is None:
            raise abort(404)
        return jsonify(variable)

    @app.route('/spec')
    def get_spec():
        # Ugly Python2-compatible way
        response = {}
        response.update(data['openAPI_spec'])
        response.update({'host': request.host_url})
        return jsonify(response)

        # Nice Python3 syntax, but doesn't work in Python 2
        # return jsonify({**data['openAPI_spec'], **{'host': request.host_url}})

    def handle_invalid_json(error):
        json_response = jsonify({
            'error': 'Invalid JSON: {}'.format(error.args[0]),
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
        except UnicodeEncodeError as e:
            abort(make_response(jsonify({"error": "'" + e[1] + "' is not a valid ASCII value."}), 400))

        requested_computations = dpath.util.search(input_data, '*/*/*/*', afilter = lambda t: t is None, yielded = True)
        results = {}

        try:
            for computation in requested_computations:
                path = computation[0]
                entity_plural, entity_id, variable_name, period = path.split('/')
                variable = tax_benefit_system.get_variable(variable_name)
                result = simulation.calculate(variable_name, period)
                entity = simulation.get_entity(plural = entity_plural)
                entity_index = entity.ids.index(entity_id)

                if variable.value_type == Enum:
                    entity_result = result.decode()[entity_index].name
                elif variable.value_type == float:
                    entity_result = float(str(result[entity_index]))  # To turn the float32 into a regular float without adding confusing extra decimals. There must be a better way.
                else:
                    entity_result = result.tolist()[entity_index]

                dpath.util.new(results, path, entity_result)

        except UnicodeEncodeError as e:
            abort(make_response(jsonify({"error": "'" + e[1] + "' is not a valid ASCII value."}), 400))

        dpath.util.merge(input_data, results)

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
            simulation.calculate(variable_name, period)

        trace = deepcopy(simulation.tracer.trace)
        for vector_key, vector_trace in trace.items():
            value = vector_trace['value'].tolist()
            if isinstance(value[0], Enum):
                value = [item.name for item in value]
            vector_trace['value'] = value

        return jsonify({
            "trace": trace,
            "entitiesDescription": {entity.plural: entity.ids for entity in simulation.entities.values()},
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
                source_ip = ""
            elif request.headers.get('X-Forwarded-For'):
                source_ip = request.headers['X-Forwarded-For'].split(', ')[0]
            else:
                source_ip = request.remote_addr

            api_version = "{}-{}".format(data['country_package_metadata']['name'],
                                         data['country_package_metadata']['version'])

            tracker.track(request.url, source_ip, api_version, request.path)
        return response

    @app.errorhandler(500)
    def internal_server_error(e):
        message = to_unicode(e.args[0])
        if type(e) == UnicodeEncodeError or type(e) == UnicodeDecodeError:
            response = jsonify({"error": "Internal server error: '" + e[1] + "' is not a valid ASCII value."})
        elif message:
            response = jsonify({"error": "Internal server error: " + message.strip(os.linesep).replace(os.linesep, ' ')})
        else:
            response = jsonify({"error": "Internal server error: " + str(e)})
        response.status_code = 500
        return response

    return app
