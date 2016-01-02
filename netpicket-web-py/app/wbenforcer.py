# -*- coding: utf-8 -*-
"""
Given a buoy's info checks whether it should be an info, warning or
alert message.
"""
import datetime
from app import red
import app.models as models
import app.const as const


def generate_alerts(apik, buoy_content):
    """Generates alerts, warnings and info messages."""
    queue = red.pubsub()
    buoy = models.get_api_key(apik)
    entries_network = models.get_entries_network(buoy['network'])
    scantime = datetime.datetime.strptime(buoy_content['scan-time'],
                                          const.STRTIME_KEY_GENERATED)
    net = models.get_network(buoy['network'])
    date = scantime.strftime(const.STRTIME_DATE)
    time = scantime.strftime(const.STRTIME_TIME)
    day = scantime.strftime(const.STRTIME_DAY)
    # needs 'text' and 'priority'
    message = {'date': date, 'time': time, 'day': day,
               'netid': net['id'], 'netname': net['name']}
    for host in buoy_content['up']:
        found = False
        for entry in entries_network:
            if host['mac'] in entry['mac'] or host['mac'] in entry['address']:
                found = True
                if entry['type'] == 'B':
                    # danger: R
                    if host['mac-vendor'] and len(host['mac-vendor']) > 0:
                        text = 'Blacklisted host {0} ({1} - {2}) connected'
                        text = text.format(host['address'], host['mac'],
                                           host['mac-vendor'])
                    else:
                        text = 'Blacklisted host {0} ({1}) connected'.format(
                            host['address'], host['mac'])
                    message['text'] = text
                    message['priority'] = 'R'
                    print " [RED] send", message
                    red.publish(const.CHAN_TIMELINE, message)
                else:
                    # info: B
                    if host['mac-vendor'] and len(host['mac-vendor']) > 0:
                        text = 'Known host {0} ({1} - {2}) connected'.format(
                            host['address'], host['mac'], host['mac-vendor'])
                    else:
                        text = 'Known host {0} ({1}) connected'.format(
                            host['address'], host['mac'])
                    message['text'] = text
                    message['priority'] = 'B'
                    print " [RED] send", message
                    red.publish(const.CHAN_TIMELINE, message)
                break
        if not found:
            if host['mac'] and len(host['mac']) > 0:
                if host['mac-vendor'] and len(host['mac-vendor']) > 0:
                    text = 'Unknonw host {0} ({1} - {2}) connected'.format(
                         host['address'], host['mac'], host['mac-vendor'])
                else:
                    text = 'Unknonw host {0} ({1}) connected'.format(
                        host['address'], host['mac'])
            else:
                text = 'Unknonw host {0} connected'.format(host['address'])
            message['text'] = text
            message['priority'] = 'O'
            print " [RED] send", message
            red.publish(const.CHAN_TIMELINE, message)
    for hostmac in buoy_content['down']:
        found = False
        for entry in entries_network:
            if hostmac in entry['mac'] or hostmac in entry['address']:
                found = True
                if entry['type'] == 'B':
                    # danger: R
                    text = 'Blacklisted host ({0}) disconnected'.format(hostmac)
                    message['text'] = text
                    message['priority'] = 'R'
                    print " [RED] send", message
                    red.publish(const.CHAN_TIMELINE, message)
                else:
                    # info: B
                    text = 'Known host ({0}) disconnected'.format(hostmac)
                    message['text'] = text
                    message['priority'] = 'B'
                    print " [RED] send", message
                    red.publish(const.CHAN_TIMELINE, message)
                break
        if not found:
            # warning: O
            text = 'Unknonw host ({0}) disconnected'.format(hostmac)
            message['text'] = text
            message['priority'] = 'O'
            print " [RED] send", message
            red.publish(const.CHAN_TIMELINE, message)
    print " [RED] end"
