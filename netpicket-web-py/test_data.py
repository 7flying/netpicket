# -*- coding: utf-8 -*-
"""
Generates testing data.
"""

import random, datetime, itertools
import app.models as models
import app.const as const

def generate_mockup_data(networks=2, days=3, events_day=10):
    """Generate mockup data."""
    users = models.User.query.all()
    for user in users:
        for net in range(networks):
            dns2 = '8.8.8.8.6' if net % 2 == 0 else None
            models.set_network(str(user.id), 'Home ' + str(net +1),
                               'eth' + str(net +1),
                               'FC:AA:25:32:FC:' + str(random.randint(10, 32)),
                               '1000 Mb/s', 'None',
                               '192.168.1.' + str(random.randint(1, 254)),
                               '255.255.255.0', '192.168.1.1', '8.8.8.8.8',
                               dns2=dns2)
            now = datetime.datetime.now()
            for day in range(days):
                then = now - datetime.timedelta(days=day)
                for _ in itertools.repeat(None, events_day):
                    for network in models.get_user_networks(user.id):
                        models.save_event(user.id, network, 'Event ' + str(random.randint(1, 100)),
                                          then.strftime(const.STRTIME_DATE),
                                          then.strftime(const.STRTIME_DAY),
                                          then.strftime(const.STRTIME_TIME),
                                          const.PRIORITY_COLOUR[
                                              random.randint(0, 3)])

if __name__ == '__main__':
    generate_mockup_data()
