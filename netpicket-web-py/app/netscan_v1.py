# -*- coding: utf-8 -*-
"""
REST api consumed by the buoys.
"""
from flask import jsonify, Blueprint

netscan_api = Blueprint('netscan_api', __name__, url_prefix='/netscan/v1')


@netscan_api.route('/work', methods=['GET', 'POST'])
def work():
    return jsonify({'status': 200, 'message': 'ok'})

