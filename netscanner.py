# -*- coding: utf-8 -*-
"""
Buoy's scanning process.
"""
import threading, sys, datetime, Queue, sched, time, requests, urllib, json

from libnmap.process import NmapProcess
from libnmap.parser import NmapParser, NmapParserException

DATETIME_FORMAT = '%d/%m/%Y - %-H:%M'

class NetScanner(object):
    """Network scanner"""

    _RESULTS = Queue.Queue()
    _WORK = Queue.Queue()

    def __init__(self, key, net):
        self.running = False
        self.net = net
         # Records the last hosts who where online
        self.online = []
        self.uuid = key
        self.url = 'http://127.0.0.1:8000/netscan/v1/work/' + self.uuid

    def _scanner(self, option='-sn'):
        """Scans the network"""
        nmap = NmapScanner(self.net)
        success, data = nmap.scan(option)
        # data has: 'scan-time' and 'hosts'
        if success:
            results = {'up': [], 'down': [], 'scan-time': data['scan-time']}
            for host in data['hosts']:
                prev = False
                results['up'].append(host)
                if host['mac'] and len(host['mac']) > 0:
                    if host['mac'] in self.online:
                        self.online.remove(host['mac'])
                        prev = True
                if not prev and host['address'] in self.online:
                    self.online.remove(host['address'])
            results['down'] = self.online
            for host in results['up']:
                if host['mac'] and len(host['mac']) > 0:
                    self.online.append(host['mac'])
                else:
                    self.online.append(host['address'])
            NetScanner._RESULTS.put(results)

    def _gateway(self, scheduler):
        """Puts jobs for the scanner and checks the server"""
        # Check if we have results to send
        result = None
        try:
            result = NetScanner._RESULTS.get(True, 10)
        except Queue.Empty:
            pass
        if result:
            # send results to server
            headers = {'Content-Type': 'application/json'}
            response = requests.post(self.url, data=json.dumps(result),
                                     headers=headers)
            if response.status_code != 200:
                NetScanner._RESULTS.put(result)
        # Check if we have job to do
        response = urllib.urlopen(self.url)
        jsondata = json.loads(response.read())
        if jsondata['status'] == 200:
            if jsondata['order'] == 'stop':
                # clean cache
                self.online = []
            elif jsondata['order'] == 'launch':
                if jsondata['time'] == 0:
                    self._launch_scanner()
            # Prepare the scheduler again to keep calling this method because
            # we have received a 200
            scheduler.enter(1 * 30, 1, self._gateway, (scheduler,))
        else:
            print " INFO: Netscanner shutting down. API key has been deleted."

    def _gateway_timer(self):
        scheduler = sched.scheduler(time.time, time.sleep)
        scheduler.enter(0, 1, self._gateway, (scheduler,))
        scheduler.run()

    def _launch_gateway(self):
        """Producer. Checks Netpicket server to receive orders, orders scanner
        to scan stuff.
        """
        producer = threading.Thread(target=self._gateway_timer,
                                    name="Netpicket-Gateway-Thread")
        producer.start()

    def _launch_scanner(self):
        """Consumer. Receives scan requests from the gateway thread."""
        consumer = threading.Thread(target=self._scanner,
                                    name="Netpicket-Scanner-Thread")
        consumer.daemon = True
        consumer.start()

    def start(self):
        """Starts the network scanning process."""
        if not self.running:
            if not self.uuid:
                print " ERROR: Netpicket API key not found"
            else:
                self.running = True
                self._launch_gateway()

class NmapScanner(object):
    """Nmap scanner."""

    def __init__(self, net):
        self.net = net

    def scan(self, option):
        """Scans the net with the given option."""
        proc = NmapProcess(self.net, option)
        ret = proc.run()
        if ret == 0:
            try:
                parsed = NmapParser.parse(proc.stdout)
                output = self._extract_data(parsed)
                return (True, output)
            except NmapParserException:
                return (False, None)
        else:
            return (False, None)

    def _extract_data(self, parsed_scan, option='-sn'):
        """Extracts data from a parsed scan. Only 'up' hosts' info is taken."""
        now = datetime.datetime.now()
        data = {'scan-time': now.strftime(DATETIME_FORMAT)}
        ret = []
        for host in parsed_scan.hosts:
            if host.status in 'up':
                tmphost = {}
                if len(host.hostnames) > 0:
                    tmphost['hostname'] = host.hostnames.pop()
                else:
                    tmphost['hostname'] = None
                tmphost['address'] = host.address
                tmphost['mac'] = host.mac
                tmphost['mac-vendor'] = host.vendor
                # TODO other options may have more data, parse such data here
                print tmphost
                ret.append(tmphost)
        data['hosts'] = ret
        return data

if __name__ == '__main__':
    BUOY = NetScanner(sys.argv[1], sys.argv[2])
    BUOY.start()
