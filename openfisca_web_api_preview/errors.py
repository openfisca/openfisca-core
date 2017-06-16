# -*- coding: utf-8 -*-

from flask import jsonify, make_response, abort


def handle_invalid_json(error):
    json_response = jsonify({
        'error': 'Invalid JSON: {}'.format(error.message),
        })

    abort(make_response(json_response, 400))
