"""This module offers facilities to initialize a WindowsInterpreter
based on libvirt automation.

"""

import re

from xml.etree import ElementTree

import libvirt


from murphy.automation.control import LibvirtControl
from murphy.automation.feedback import LibvirtFeedback
# from murphy.model.scrapers.winapi import WinAPIScraper
from murphy.model.scrapers.uiauto import WinUIAutomationScraper
from murphy.model.interpreters.windows import WindowsInterpreter, Tolerance


def state_interpreter(
        domain_id: (int, str), scraper_port: int = 8000) -> WindowsInterpreter:
    """Returns a WindowsInterpreter based on libvirt."""
    domain = libvirt_domain(domain_id)
    address = domain_address(domain)
    vnc_server = domain_vnc_server(domain)

    control = LibvirtControl(vnc_server, domain_id)
    feedback = LibvirtFeedback(vnc_server, domain_id)
    scraper = WinUIAutomationScraper(address, scraper_port, full_scrape=True)
    tolerance = Tolerance(1.6, (0.35, 0.2, 0.18))
    # As the WinAPI scraper does not report toggled checkboxes,
    # a lower image comparison tolerance is recommended
    # scraper = WinAPIScraper(address, scraper_port)
    # tolerance = Tolerance(1.0, (0.20, 0.1, 0.18))

    interpreter = WindowsInterpreter(feedback, control, scraper)
    interpreter.tolerance = tolerance

    return interpreter


def domain_address(domain: libvirt.virDomain) -> str:
    interfaces = domain.interfaceAddresses(
        libvirt.VIR_DOMAIN_INTERFACE_ADDRESSES_SRC_LEASE)

    for iface in interfaces.values():
        if isinstance(iface, dict) and 'addrs' in iface:
            for address in iface['addrs']:
                if 'addr' in address:
                    return address['addr']

    raise RuntimeError("No IP address found for the given domain")


def domain_vnc_server(domain: libvirt.virDomain) -> str:
    etree = ElementTree.fromstring(domain.XMLDesc())

    vnc = etree.find('.//graphics[@type="vnc"]')
    if vnc is None:
        raise RuntimeError("No VNC connection found for the given domain")

    if 'socket' in vnc.keys():
        return vnc.get('socket')
    elif {'listen', 'port'} <= set(vnc.keys()):
        return '::'.join((vnc.get('listen'), vnc.get('port')))
    else:
        raise RuntimeError("No valid VNC connection found for the given domain")


def libvirt_domain(domain_id: (int, str)) -> libvirt.virDomain:
    connection = libvirt.open(QEMU_URI)

    if isinstance(domain_id, int):
        return connection.lookupByID(domain_id)
    elif re.match(UUID_EXPR, domain_id):
        return connection.lookupByUUIDString(domain_id)
    else:
        return connection.lookupByName(domain_id)


QEMU_URI = 'qemu:///system'
UUID_EXPR = "[a-fA-F0-9]{8}-[a-fA-F0-9]{4}-4[a-fA-F0-9]{3}-" + \
            "[89aAbB][a-fA-F0-9]{3}-[a-fA-F0-9]{12}"
