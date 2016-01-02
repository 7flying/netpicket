# -*- coding: utf-8 -*-
"""
Manages the actions of the buoys
"""
import app.models as models
import app.const as const

def set_action(buoy_id, action, now=False):
    """Orders the given action to the buoy."""
    if action == const.BUOY_AC_LAUNCH:
        _set_launch(buoy_id, now)
    elif action == const.BUOY_AC_STOP:
        _set_stop(buoy_id)

def _set_stop(buoy_id):
    """Orders a buoy to stop scanning."""
    models.change_status(buoy_id, const.BUOY_STOPPED)
    models.set_action_buoy(buoy_id, const.BUOY_AC_STOP)

def _set_launch(buoy_id, now):
    """Orders a buoy to start scanning."""
    models.change_status(buoy_id, const.BUOY_ACTIVE)
    models.set_action_buoy(buoy_id, const.BUOY_AC_LAUNCH, now)
