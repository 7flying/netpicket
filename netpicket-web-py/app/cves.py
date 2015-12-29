# -*- coding: utf-8 -*-
"""
Checks vulneravilities in the known hosts' services.
"""
import urllib, json
import app.const as const
import app.models as models

def check_cves():
    """Checks the latest CVEs in cvedetails page."""
    status = 200
    response = urllib.urlopen(const.CVE_API)
    data = json.loads(response.read())
    if data is None:
        status = 400
    if status == 400:
        return {'status' : status}
    return {'status' : status, 'data' : data}

def check_vulns(latest_cves):
    """Checks if the services in the db are vulnerable to the given CVEs."""
    services = models.get_services()
    vulns = dict(zip(services, [False for _ in services]))
    for serv in services:
        for cve in latest_cves:
            if serv.lower() in cve['summary'].lower():
                if not vulns[serv]:
                    vulns[serv] = []
                vulns[serv].append(cve['cve_id'])
    return vulns
