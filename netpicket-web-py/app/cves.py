# -*- coding: utf-8 -*-
"""
Checks vulneravilities in the known hosts' services.
"""
import re
import app.models as models

def check_vulns(latest_cves):
    """Checks if the services in the db are vulnerable to the given CVEs."""
    services = models.get_services()
    vulns = dict(zip(services, [False for _ in services]))
    for serv in services:
        for cve in latest_cves:
            if re.match(serv.lower(), cve['summary'].lower(), re.IGNORECASE):
                if not vulns[serv]:
                    vulns[serv] = []
                vulns[serv].append(cve['cve_id'])
    return vulns
