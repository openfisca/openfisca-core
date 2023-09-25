import logging
import os
import traceback

from openfisca_core import errors as core_errors

from . import errors, handlers, loader

try:
    import flask
    import flask_cors
    import werkzeug.exceptions
    from werkzeug.middleware import proxy_fix

except ImportError as error:
    errors.handle_import_error(error)

log = logging.getLogger("gunicorn.error")


def init_tracker(url, idsite, tracker_token):
    try:
        from openfisca_tracker import piwik

        tracker = piwik.PiwikTracker(url, idsite, tracker_token)

        message = (
            "You chose to activate the `tracker` module. ",
            "Tracking data will be sent to: " + url,
            "For more information, see <https://github.com/openfisca/openfisca-core#tracker-configuration>.",
        )

        log.info(os.linesep.join(message))

        return tracker

    except ImportError:
        message = (
            traceback.format_exc(),
            "You chose to activate the `tracker` module, but it is not installed.",
            "For more information, see <https://github.com/openfisca/openfisca-core#tracker-installation>.",
        )

        log.warn(os.linesep.join(message))


def create_app(
    tax_benefit_system,
    tracker_url=None,
    tracker_idsite=None,
    tracker_token=None,
    welcome_message=None,
):
    if not tracker_url or not tracker_idsite:
        tracker = None

    else:
        tracker = init_tracker(tracker_url, tracker_idsite, tracker_token)

    app = flask.Flask(__name__)

    # Fix flask.request.remote_addr to get the real client IP address.
    app.wsgi_app = proxy_fix.ProxyFix(app.wsgi_app, x_for=1, x_host=1)

    # Set cors config to handle jsonp.
    flask_cors.CORS(app, origins="*")

    # When False, lets flask.jsonify encode to utf-8.
    app.config["JSON_AS_ASCII"] = False

    # Accept url like /parameters/.
    app.url_map.strict_slashes = False

    # Do not eliminate // in paths.
    app.url_map.merge_slashes = False

    # Don't sort JSON keys in the Web API.
    app.config["JSON_SORT_KEYS"] = False

    data = loader.build_data(tax_benefit_system)

    DEFAULT_WELCOME_MESSAGE = "This is the root of an OpenFisca Web API. To learn how to use it, check the general documentation (https://openfisca.org/doc/) and the OpenAPI specification of this instance ({}spec)."

    @app.before_request
    def before_request():
        if flask.request.path != "/" and flask.request.path.endswith("/"):
            return flask.redirect(flask.request.path[:-1])

    @app.route("/")
    def get_root():
        return (
            flask.jsonify(
                {
                    "welcome": welcome_message
                    or DEFAULT_WELCOME_MESSAGE.format(flask.request.host_url)
                }
            ),
            300,
        )

    @app.route("/parameters")
    def get_parameters():
        parameters = {
            parameter["id"]: {
                "description": parameter["description"],
                "href": f"{flask.request.host_url}parameter/{name}",
            }
            for name, parameter in data["parameters"].items()
            if parameter.get("subparams")
            is None  # For now and for backward compat, don't show nodes in overview
        }

        return flask.jsonify(parameters)

    @app.route("/parameter/<path:parameter_id>")
    def get_parameter(parameter_id):
        parameter = data["parameters"].get(parameter_id)

        if parameter is None:
            # Try legacy route
            parameter_new_id = parameter_id.replace(".", "/")
            parameter = data["parameters"].get(parameter_new_id)

        if parameter is None:
            raise flask.abort(404)

        return flask.jsonify(parameter)

    @app.route("/variables")
    def get_variables():
        variables = {
            name: {
                "description": variable["description"],
                "href": f"{flask.request.host_url}variable/{name}",
            }
            for name, variable in data["variables"].items()
        }

        return flask.jsonify(variables)

    @app.route("/variable/<id>")
    def get_variable(id):
        variable = data["variables"].get(id)

        if variable is None:
            raise flask.abort(404)

        return flask.jsonify(variable)

    @app.route("/entities")
    def get_entities():
        return flask.jsonify(data["entities"])

    @app.route("/spec")
    def get_spec():
        scheme = flask.request.environ["wsgi.url_scheme"]
        host = flask.request.host
        url = f"{scheme}://{host}"

        return flask.jsonify(
            {
                **data["openAPI_spec"],
                **{"servers": [{"url": url}]},
            }
        )

    def handle_invalid_json(error):
        json_response = flask.jsonify(
            {
                "error": f"Invalid JSON: {error.args[0]}",
            }
        )

        flask.abort(flask.make_response(json_response, 400))

    @app.route("/calculate", methods=["POST"])
    def calculate():
        tax_benefit_system = data["tax_benefit_system"]
        flask.request.on_json_loading_failed = handle_invalid_json
        input_data = flask.request.get_json()

        try:
            result = handlers.calculate(tax_benefit_system, input_data)

        except (
            core_errors.SituationParsingError,
            core_errors.PeriodMismatchError,
        ) as e:
            flask.abort(flask.make_response(flask.jsonify(e.error), e.code or 400))

        except (UnicodeEncodeError, UnicodeDecodeError) as e:
            flask.abort(
                flask.make_response(
                    flask.jsonify(
                        {"error": "'" + e[1] + "' is not a valid ASCII value."}
                    ),
                    400,
                )
            )

        return flask.jsonify(result)

    @app.route("/trace", methods=["POST"])
    def trace():
        tax_benefit_system = data["tax_benefit_system"]
        flask.request.on_json_loading_failed = handle_invalid_json
        input_data = flask.request.get_json()

        try:
            result = handlers.trace(tax_benefit_system, input_data)

        except (
            core_errors.SituationParsingError,
            core_errors.PeriodMismatchError,
        ) as e:
            flask.abort(flask.make_response(flask.jsonify(e.error), e.code or 400))

        return flask.jsonify(result)

    @app.after_request
    def apply_headers(response):
        response.headers.extend(
            {
                "Country-Package": data["country_package_metadata"]["name"],
                "Country-Package-Version": data["country_package_metadata"]["version"],
            }
        )

        return response

    @app.after_request
    def track_requests(response):
        if tracker:
            if flask.request.headers.get("dnt"):
                source_ip = ""

            elif flask.request.headers.get("X-Forwarded-For"):
                source_ip = flask.request.headers["X-Forwarded-For"].split(", ")[0]

            else:
                source_ip = flask.request.remote_addr

            api_version = "{}-{}".format(
                data["country_package_metadata"]["name"],
                data["country_package_metadata"]["version"],
            )

            tracker.track(flask.request.url, source_ip, api_version, flask.request.path)

        return response

    @app.errorhandler(500)
    def internal_server_error(e: werkzeug.exceptions.InternalServerError):
        message = getattr(e, "original_exception", e.description)
        response = flask.jsonify({"error": "Internal server error: " + str(message)})
        response.status_code = 500
        return response

    return app
