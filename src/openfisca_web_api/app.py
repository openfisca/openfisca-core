# -*- coding: utf-8 -*-

import logging
import os
import traceback

from openfisca_core.errors import SituationParsingError, PeriodMismatchError
from openfisca_web_api.loader import build_data
from openfisca_web_api.errors import handle_import_error
from openfisca_web_api import handlers

try:
    from flask import Flask, jsonify, abort, request, make_response
    from flask_cors import CORS
    from werkzeug.middleware.proxy_fix import ProxyFix
    import werkzeug.exceptions
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
    # Fix request.remote_addr to get the real client IP address
    app.wsgi_app = ProxyFix(app.wsgi_app, x_for = 1, x_host = 1)
    CORS(app, origins = '*')

    app.config['JSON_AS_ASCII'] = False  # When False, lets jsonify encode to utf-8
    app.url_map.strict_slashes = False  # Accept url like /parameters/
    app.url_map.merge_slashes = False  # Do not eliminate // in paths
    app.config['JSON_SORT_KEYS'] = False  # Don't sort JSON keys in the Web API

    data = build_data(tax_benefit_system)

    DEFAULT_WELCOME_MESSAGE = "This is the root of an OpenFisca Web API. To learn how to use it, check the general documentation (https://openfisca.org/doc/) and the OpenAPI specification of this instance ({}spec)."

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

    @app.route('/entities')
    def get_entities():
        return jsonify(data['entities'])

    @app.route('/spec')
    def get_spec():
        return jsonify({
            **data['openAPI_spec'],
            **{'host': request.host},
            **{'schemes': [request.environ['wsgi.url_scheme']]}
            })

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
            result = handlers.calculate(tax_benefit_system, input_data)
        except (SituationParsingError, PeriodMismatchError) as e:
            abort(make_response(jsonify(e.error), e.code or 400))
        except (UnicodeEncodeError, UnicodeDecodeError) as e:
            abort(make_response(jsonify({"error": "'" + e[1] + "' is not a valid ASCII value."}), 400))
        return jsonify(result)

    @app.route('/trace', methods=['POST'])
    def trace():
        tax_benefit_system = data['tax_benefit_system']
        request.on_json_loading_failed = handle_invalid_json
        input_data = request.get_json()
        try:
            result = handlers.trace(tax_benefit_system, input_data)
        except (SituationParsingError, PeriodMismatchError) as e:
            abort(make_response(jsonify(e.error), e.code or 400))
        return jsonify(result)

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
    def internal_server_error(e: werkzeug.exceptions.InternalServerError):
        message = getattr(e, "original_exception", e.description)
        response = jsonify({"error": "Internal server error: " + str(message)})
        response.status_code = 500

        return response

    return app
