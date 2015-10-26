# -*- coding: utf-8 -*-

import netifaces

from libnmap.process import NmapProcess
from libnmap.parser import NmapParser, NmapParserException


def get_network_buoy_info(interface):
    """Returns info about the network and buoy in the given net interface."""
    ret = {}
    n_info = netifaces.interfaces().get(interface)
    if n_info:
        """
        AF_LINK: {17: [{'broadcast': 'ff:ff:ff:ff:ff:ff',
                        'addr': 'a0:ce:c8:05:35:f9'}],
        AF_INET:  2: [{'broadcast': '10.172.203.255', 'netmask': '255.255.255.0',
                       'addr': '10.172.203.199'}],
        AF_INET6: 10: [{'netmask': 'ffff:ffff:ffff:ffff::',
                        'addr': 'fe80::a2ce:c8ff:fe05:35f9%eth1'}]}
        """
        # Get the addresses for the given interface
        ret['AF_INET'] = n_info.get(netifaces.AF_INET) # IPv4
        ret['AF_INET6'] = n_info.get(netifaces.AF_INET6) # IPv6
        ret['AF_LINK'] = n_info[netifaces.AF_LINK] # link layer interface
        """
        {2: [('10.0.1.1', 'en0', True), ('10.2.1.1', 'en1', False)],
         30: [('fe80::1', 'en0', True)],
         'default': { 2: ('10.0.1.1', 'en0'), 30: ('fe80::1', 'en0') }}
        """
        # Get the default gateways for IPv4 and IPv6
        ret['gateways'] = {}
        ret['gateways']['AF_INET'] = netifaces.gateways()['default'].get(
            netifaces.AF_INET)
        ret['gateways']['AF_INET6'] = netifaces.gateways()['default'].get(
            netifaces.AF_INET6)
    return ret

def host_discovery(network):
    """Performs host discovery in the given network.
    :param network: string
    """
    re = _run_scan(network, "-sn")
    return re


def _run_scan(targets, options):
    """Runs a nmap scan with the given options, returns a report for the given
    scan.
    """
    parsed = None
    nmproc = NmapProcess(targets, options)
    return_code = nmproc.run()
    if return_code == 0:
        try:
            parsed = NmapParser.parse(nmproc.stdout)
            return parsed
        except NmapParserException as e:
            print "scan failed: {0}".format(nmproc.stderr)
    return 1


def print_scan(nmap_report):
    """Print the results of the report."""
    print("Starting Nmap {0} ( http://nmap.org ) at {1}".format(
        nmap_report.version,
        nmap_report.started))

    for host in nmap_report.hosts:
        if len(host.hostnames):
            tmp_host = host.hostnames.pop()
        else:
            tmp_host = host.address

        print("Nmap scan report for {0} ({1})".format(
            tmp_host,
            host.address))
        print "Host is {0}.".format(host.status)
        print "  PORT     STATE         SERVICE"

        for serv in host.services:
            pserv = "{0:>5s}/{1:3s}  {2:12s}  {3}".format(str(serv.port),
                                                          serv.protocol,
                                                          serv.state,
                                                          serv.service)
            if len(serv.banner):
                pserv += " ({0})".format(serv.banner)
            print pserv
    print nmap_report.summary


if __name__ == "__main__":
    report = _run_scan("127.0.0.1", "-sV")
    if report:
        print_scan(report)
    else:
        print "Something went wrong"
