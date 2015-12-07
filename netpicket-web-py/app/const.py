# -*- coding: utf-8 -*-
"""
Holds the app's constants.
"""

## Date-time formats
# For instance, 20151121
STRTIME_DATE = '%Y%m%d'
# Time, remove first zero, 09:12 -> 9:12
STRTIME_TIME = '%-H:%M'
# Wed 24 Oct
STRTIME_DAY = '%a %-d %b'

# Priorities
PRIORITIES = {0: 'Info', 1: 'Low', 2: 'Medium', 3: 'High'}
PRIORITY_COLOUR = {0: 'G', 1: 'B', 2: 'O', 3: 'R'}

# Timeline days
TIMELINE_DAYS = 3

# Section names
SEC_TIMELINE = 'timeline'
SEC_ALERTS = 'alerts'
SEC_NETWORKS = 'networks'
SEC_ACLS = 'wblists'
SEC_SCANS = 'scans'
SEC_STATS = 'stats'


# Template alert categories
ALERT_SUCCESS = 'alert alert-success'
ALERT_ERROR = 'alert alert-danger'
ALERT_WARNING = 'alert alert-warning'
ALERT_INFO = 'alert alert-info'
