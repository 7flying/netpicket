# -*- coding: utf-8 -*-
"""
Manages the actions of the buoys
"""
import app.models as models
import app.const as const

def set_action(buoy_id, action):
    """Orders the given action to the buoy."""
    if action == const.BUOY_AC_LAUNCH:
        models.change_status(buoy_id, const.BUOY_ACTIVE)
    elif action == const.BUOY_AC_STOP:
        models.change_status(buoy_id, const.BUOY_STOPPED)

def _set_stop(buoy_id):
    """Orders a buoy to stop scanning."""
    # TODO
    pass

def _set_launch(buoy_id):
    """Orders a buoy to start scanning."""
    # TODO
    pass
