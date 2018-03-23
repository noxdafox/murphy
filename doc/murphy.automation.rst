Mr. Murphy Automation
=====================

Facilities for interacting with a Device.

A Device can be either a physical computer, a mobile device or a virtual machine.
The APIs are designed to be agnostic to the type of Device they interact with.

Interfaces
----------

The interface API contracts can be found in the module `automation/interfaces.py`.

The interfaces are grouped in two categories: Feedback and Control.

Feedback
++++++++

The Feedback class provides facilities for reading the state of a Device in order to interpret the execution of the GUI software.

The Feedback class abstracts interfaces such as the Screen and the Device Load Average.

.. autoclass:: murphy.automation.Feedback
    :members:
    :undoc-members:
    :show-inheritance:
    :special-members:
    :exclude-members: __dict__, __weakref__, __module__, __init__

.. autoclass:: murphy.automation.Screen
    :members:
    :undoc-members:
    :show-inheritance:
    :special-members:
    :exclude-members: __dict__, __weakref__, __module__, __init__

.. autoclass:: murphy.automation.LoadAverage
    :members:
    :undoc-members:
    :show-inheritance:
    :special-members:
    :exclude-members: __dict__, __weakref__, __module__, __init__

Control
+++++++

The Control class allows to alter the state of the Device to drive the execution of the GUI software.

The Control class abstracts interfaces such as generic input devices (Mouse and Keyboard) and execution checkpoints.

.. autoclass:: murphy.automation.Control
    :members:
    :undoc-members:
    :show-inheritance:
    :special-members:
    :exclude-members: __dict__, __weakref__, __module__, __init__

.. autoclass:: murphy.automation.Mouse
    :members:
    :undoc-members:
    :show-inheritance:
    :special-members:
    :exclude-members: __dict__, __weakref__, __module__, __init__

.. autoclass:: murphy.automation.Keyboard
    :members:
    :undoc-members:
    :show-inheritance:
    :special-members:
    :exclude-members: __dict__, __weakref__, __module__, __init__

.. autoclass:: murphy.automation.DeviceState
    :members:
    :undoc-members:
    :show-inheritance:
    :special-members:
    :exclude-members: __dict__, __weakref__, __module__, __init__

Factory interface
-----------------

.. autoclass:: murphy.automation.MurphyFactory
    :members:
    :undoc-members:
    :show-inheritance:
    :special-members:
    :exclude-members: __dict__, __weakref__, __module__, __init__

Available Implementations
-------------------------

Additionally, the automation module offers the following implementations of the above mentioned interfaces.

Feedback and Control
++++++++++++++++++++

.. automodule:: murphy.automation.control
    :members:
    :undoc-members:
    :show-inheritance:
    :special-members:
    :exclude-members: __dict__, __weakref__, __module__, __init__

.. automodule:: murphy.automation.feedback
    :members:
    :undoc-members:
    :show-inheritance:
    :special-members:
    :exclude-members: __dict__, __weakref__, __module__, __init__

Subclasses
++++++++++

.. toctree::

    murphy.automation.vnc
    murphy.automation.libvirt
