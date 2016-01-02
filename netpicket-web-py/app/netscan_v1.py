# -*- coding: utf-8 -*-
"""
REST api consumed by the buoys.
"""
import datetime
from flask import jsonify, request, Blueprint
from app import red
import models, const

netscan_api = Blueprint('netscan_api', __name__, url_prefix='/netscan/v1')

@netscan_api.route('/work/<uuid>', methods=['GET', 'POST'])
def work(uuid):
    """The buoys request work and post work results to this method."""
    buoy_id = models.apik_of_uuid(uuid)
    if request.method == 'GET':
        action = models.get_action_buoy(buoy_id)
        time = -1
        if action and action['action'] == const.BUOY_AC_LAUNCH:
            if action['time'] == '':
                time = 0
                models.set_action_buoy(buoy_id, const.BUOY_AC_LAUNCH)
            else:
                # If more than 7 minutes have passed from the last action
                # the buoy will perform the action, else continue waiting
                date_obj = datetime.datetime.strptime(
                    action['time'], const.STRTIME_KEY_GENERATED)
                now = datetime.datetime.now()
                if (now-date_obj).total_seconds() / 60 >= 7:
                    time = 0
                    # Update when the last action mas made (now)
                    models.set_action_buoy(buoy_id, const.BUOY_AC_LAUNCH)
            return jsonify({'status': 200, 'order': action['action'],
                            'time': time})
        elif action and action['action'] == const.BUOY_AC_STOP:
            return jsonify({'status': 200, 'order': action['action']})
        else:
            return jsonify({'status': 404})
    elif request.method == 'POST':
        content = request.get_json()
        print content
        return jsonify({'status': 404, 'message': 'o'})

