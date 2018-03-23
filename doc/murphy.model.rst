Mr. Murphy Model
================

The `model` module abstracts the GUI application state providing mechanisms for analysing and changing it.

A `State` comprises of a `Window` and a list of `Actions` to be performed.
States should implement comparison mechanisms to help tracing the execution of the application.

Interfaces
----------

The interface API contracts can be found in the module `model/interfaces.py`.

.. autoclass:: murphy.model.Interpreter
    :members:
    :undoc-members:
    :show-inheritance:
    :special-members:
    :exclude-members: __dict__, __weakref__, __module__, __init__

.. autoclass:: murphy.model.State
    :members:
    :undoc-members:
    :show-inheritance:
    :special-members:
    :exclude-members: __dict__, __weakref__, __module__, __init__, __hash__

.. autoclass:: murphy.model.Window
    :members:
    :undoc-members:
    :show-inheritance:
    :special-members:
    :exclude-members: __dict__, __weakref__, __module__, __init__

.. autoclass:: murphy.model.Action
    :members:
    :undoc-members:
    :show-inheritance:
    :special-members:
    :exclude-members: __dict__, __weakref__, __module__, __init__

Action types
++++++++++++

.. autoclass:: murphy.model.Button
    :members:
    :undoc-members:
    :show-inheritance:

.. autoclass:: murphy.model.Link
    :members:
    :undoc-members:
    :show-inheritance:

.. autoclass:: murphy.model.TextBox
    :members:
    :undoc-members:
    :show-inheritance:

.. autoclass:: murphy.model.ComboBox
    :members:
    :undoc-members:
    :show-inheritance:

Available Implementations
-------------------------

Additionally, the automation module offers the following implementations of the above mentioned interfaces.

.. toctree::

    murphy.model.interpreters

Scrapers
--------

The `scraper` submodule contains the client interfaces and implementations for scraping the UI content of applications.

.. toctree::

    murphy.model.scrapers
