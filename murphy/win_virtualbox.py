"""This module offers facilities to initialize a WindowsInterpreter
based on libvirt automation.

"""

from xml.etree import ElementTree

import virtualbox

from murphy.automation.control import VirtualboxControl
from murphy.automation.feedback import VirtualboxFeedback
# from murphy.model.scrapers.winapi import WinAPIScraper
from murphy.model.scrapers.uiauto import WinUIAutomationScraper
from murphy.model.interpreters.windows import WindowsInterpreter, Tolerance


def state_interpreter(
        machine_id: str, scraper_port: int = 8000) -> WindowsInterpreter:
    """Returns a WindowsInterpreter based on libvirt."""
    address = machine_address(machine_id)

    control = VirtualboxControl(machine_id)
    feedback = VirtualboxFeedback(machine_id)
    scraper = WinUIAutomationScraper(address, scraper_port, full_scrape=True)
    tolerance = Tolerance(1.6, (0.20, 0.1, 0.18))
    # As the WinAPI scraper does not report toggled checkboxes,
    # a lower image comparison tolerance is recommended
    # scraper = WinAPIScraper(address, scraper_port)
    # tolerance = Tolerance(1.0, (0.20, 0.1, 0.18))

    interpreter = WindowsInterpreter(feedback, control, scraper)
    interpreter.tolerance = tolerance

    return interpreter


def machine_address(machine_id: str) -> str:
    vbox = virtualbox.VirtualBox()
    machine = vbox.find_machine(machine_id)
    properties = machine.enumerate_guest_properties(VBOX_NETADDR_PROPERTY)

    return properties[1][0]


VBOX_NETADDR_PROPERTY = '/VirtualBox/GuestInfo/Net/0/V4/IP'
