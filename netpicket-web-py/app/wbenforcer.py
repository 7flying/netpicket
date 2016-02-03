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
    buoy = models.get_api_key(apik)
    entries_network = models.get_entries_network(buoy['network'])
    network_info = models.get_network(buoy['network'])
    scantime = datetime.datetime.strptime(buoy_content['scan-time'],
                                          const.STRTIME_KEY_GENERATED)
    net = models.get_network(buoy['network'])
    models.set_last_host_scan(apik, net['address'], scantime)
    date = scantime.strftime(const.STRTIME_DATE)
    time = scantime.strftime(const.STRTIME_TIME)
    day = scantime.strftime(const.STRTIME_DAY)
    # needs 'text' and 'priority'
    message = {'date': date, 'time': time, 'day': day,
               'netid': net['id'], 'netname': net['name']}
    for updown in ['up', 'down']:
        for host in buoy_content[updown]:
            # Mac entries in our database are lowercase
            host['mac'] = host['mac'].lower()
            # Find an entry in the w/b lists for each host
            found = False
            for entry in entries_network:
                if len(host['mac']) == 0:
                    # check if the host is the buoy
                    if host['address'] == network_info['address']:
                        found = True
                        message['priority'] = 'G'
                        message['text'] = 'Buoy {0} up and running'.format(
                            host['address'])
                        models.save_event(buoy['userid'], message['netid'],
                                          message['text'], message['date'],
                                          message['day'], message['time'],
                                          message['priority'])
                        red.publish(const.CHAN_TIMELINE, message)
                        break
                elif len(host['mac']) > 0 and host['mac'] in entry['mac']:
                    found = True
                    known = 'Blacklisted' if entry['type'] == 'B' else 'Known'
                    if host['mac-vendor'] and len(host['mac-vendor']) > 0:
                        text = '{0} host {1} ({2} - {3}) {4}'
                        text = text.format(known, host['address'], host['mac'],
                                           host['mac-vendor'], updown)
                    else:
                        if len(host['mac']) > 0:
                            text = '{0} host {1} ({2}) {3}'.format(
                                known, host['address'], host['mac'], updown)
                        else:
                            text = '{0} host {1} {2}'.format(
                                known, host['address'], updown)
                    message['text'] = text
                    # danger: Red, info Blue
                    message['priority'] = 'R' if entry['type'] == 'B' else 'B'
                    models.save_event(buoy['userid'], message['netid'],
                                      message['text'], message['date'],
                                      message['day'], message['time'],
                                      message['priority'])
                    red.publish(const.CHAN_TIMELINE, message)
                    break
            if not found:
                if host['mac'] and len(host['mac']) > 0:
                    if host['mac-vendor'] and len(host['mac-vendor']) > 0:
                        text = 'Unknown host {0} ({1} - {2}) {3}'.format(
                            host['address'], host['mac'], host['mac-vendor'],
                            updown)
                    else:
                        text = 'Unknown host {0} ({1}) {2}'.format(
                            host['address'], host['mac'], updown)
                else:
                    text = 'Unknown host {0} {1}'.format(host['address'],
                                                         updown)
                message['text'] = text
                message['priority'] = 'O'
                models.save_event(buoy['userid'], message['netid'],
                                  message['text'], message['date'],
                                  message['day'], message['time'],
                                  message['priority'])
                red.publish(const.CHAN_TIMELINE, message)
