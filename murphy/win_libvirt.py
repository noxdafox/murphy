"""This module offers facilities to initialize a WindowsInterpreter
based on libvirt automation.

"""

from xml.etree import ElementTree

import libvirt

from murphy.automation.control import LibvirtControl
from murphy.automation.feedback import LibvirtFeedback
# from murphy.model.scrapers.winapi import WinAPIScraper
from murphy.model.scrapers.uiauto import WinUIAutomationScraper
from murphy.model.interpreters.windows import WindowsInterpreter, Tolerance


def state_interpreter(
        domain_uuid: str, scraper_port: int = 8000) -> WindowsInterpreter:
    """Returns a WindowsInterpreter based on libvirt."""
    address = domain_address(domain_uuid)
    vnc_socket = domain_vnc_socket(domain_uuid)

    control = LibvirtControl(vnc_socket, domain_uuid)
    feedback = LibvirtFeedback(vnc_socket, domain_uuid)
    scraper = WinUIAutomationScraper(address, scraper_port, full_scrape=True)
    tolerance = Tolerance(1.6, (0.20, 0.1, 0.18))
    # As the WinAPI scraper does not report toggled checkboxes,
    # a lower image comparison tolerance is recommended
    # scraper = WinAPIScraper(address, scraper_port)
    # tolerance = Tolerance(1.0, (0.20, 0.1, 0.18))

    interpreter = WindowsInterpreter(feedback, control, scraper)
    interpreter.tolerance = tolerance

    return interpreter


def libvirt_cleanup(domain_uuid: str):
    connection = libvirt.open('qemu:///system')
    domain = connection.lookupByUUIDString(domain_uuid)

    for snapshot in domain.listAllSnapshots():
        snapshot.delete()


def domain_address(domain_uuid: str) -> str:
    connection = libvirt.open('qemu:///system')
    domain = connection.lookupByUUIDString(domain_uuid)
    interfaces = domain.interfaceAddresses(
        libvirt.VIR_DOMAIN_INTERFACE_ADDRESSES_SRC_LEASE)
    connection.close()

    return lookup_address(interfaces)


def lookup_address(interfaces: list) -> str:
    for iface in interfaces.values():
        if isinstance(iface, dict) and 'addrs' in iface:
            for address in iface['addrs']:
                if 'addr' in address:
                    return address['addr']

    raise RuntimeError("No IP address found for the given domain")


def domain_vnc_socket(domain_uuid: str) -> str:
    connection = libvirt.open('qemu:///system')
    domain = connection.lookupByUUIDString(domain_uuid)
    etree = ElementTree.fromstring(domain.XMLDesc())
    connection.close()

    vnc_socket = etree.find('.//graphics[@type="vnc"]').get('socket')
    if vnc_socket is None:
        raise RuntimeError("No VNC connection found for the given domain")

    return vnc_socket
