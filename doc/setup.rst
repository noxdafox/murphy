Set Up
======

Requirements
------------

 * Python > 3.5
 * A virtualization capable host
 * Libvirt and a supported hypervisor driver

   or

 * Virtualbox

Installation
------------

Please refer to your OS type and distribution manuals for setting up the chosen virtualization technology.

MrMurphy is available on PyPi.

.. code:: bash

   $ pip install mrmurphy

Environment Setup
-----------------

As Mr. Murphy tries to be the least invasive as possible, very little setup is required on the target environment.

The setup of the test environment depends on factors such as the OS platform and the type of tests which need to be performed.

The general recommendation is to reduce as much as possible the noise that other services and applications might generate. Minimizing the chance of undesired windows which could pop-up during the test execution will make the tests faster and more reliable.

Windows
+++++++

Here follows a list of Microsoft Windows requirements and known limitations.

The `Windows Update` service is known to be problematic with Mr. Murphy as it might forcefully get control of the UI or reboot the device. It is derefore, recommended to disable it during the execution of the tests.

The current implementation cannot deal with higher priviledge desktops such as the `User Account Control` (UAC) prompt.

Scrapers
********

Mr. Murphy relies on a scraper software in order to retrieve a formal description of Windows GUI contents.

There are two implementations availables in `resources/scrapers`. The `uiauto` solution is the recommended one as it supports modern GUI frameworks.

The scrapers are meant to be run within the same environment of the tested GUI applications. They implement a simple HTTP protocol allowing Mr. Murphy to retrieve the application GUI content over the network.

The User must ensure the scraper is executing within the test environment and is reachable over the network.

The simplest of the solutions would be to place a script in the Windows `startup` folder to ensure the scraper is executed at boot time.

The following Visual Basic Script can be used to start the scraper hiding the prompt window.

.. code:: powershell

    Set oShell = CreateObject ("Wscript.Shell")
    Dim strArgs
    strArgs = "cmd /c C:\start_scraper.exe parameter other_parameter"
    oShell.Run strArgs, 0, false
