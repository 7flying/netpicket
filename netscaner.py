# -*- coding: utf-8 -*-
"""
Buoy's scanning process.
"""
import threading

from libnmap.process import NmapProcess
from libnmap.parser import NmapParser, NmapParserException

class NetScanner(object):
    """Network scanner"""

    def __init__(self):
        self.running = False

    def _gateway_timer(self):
        pass

    def _scanner_timer(self):
        pass
        
    def _launch_gateway(self):
        """Producer. Checks Netpicket server to receive orders, orders scanner
        to scan stuff.
        """
        producer = threading.Thread(target=self._gateway_timer,
                                    name="Netpicket-Gateway-Thread")

    def _launch_scanner(self):
        """Consumer. Receives scan requests from the gateway thread."""
        consumer = threading.Thread(target=self._scanner_timer,
                                    name="Netpicket-Scanner-Thread")

    def start(self):
        """Starts the network scanning process."""
        if not self.running:
            self.running = True
            self._launch_scanner()
            self._launch_gateway()

class NmapScanner(object):
    """Nmap scanner."""
    
