# -*- coding: utf-8 -*-

from libnmap.process import NmapProcess
from libnmap.parser import NmapParser, NmapParserException


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
