Agent Development
=================

Agents are responsible for driving the execution of the GUI application. Therefore, their implementation vary according to the Use Case they are addressing.

The following chapter introduces a simple example of an Agent which interacts with every available object in a Windows application at most once.

Preparing the Interpreter
-------------------------

The Interpreter is responsible for constructing the GUI State and its available Actions. Interpreters offer a generic interface but their implementation depends on the Automation components which are provided. In this example, the `libvirt` and `vnc` based Automation interface will be used. Their details can be found in `murphy/automation`.

First, the `Feedback` and `Control` interfaces are built using their factory classes.

.. code:: python

    from murphy.automation.control import LibvirtControl
    from murphy.automation.feedback import LibvirtFeedback

    domain_id = "libvirt-vm-name"  # libvirt Domain ID, name or UUID
    vnc_socket = "localhost:5900"  # VNC connection socket or address

    control = LibvirtControl(vnc_socket, domain_id)
    feedback = LibvirtFeedback(vnc_socket, domain_id)

Secondly, the Windows scraper client is initialized. Mr. Murphy relies on a scraping agent running within the guest OS in order to de-construct the GUI content of a Windows application.

.. code:: python

    from murphy.model.scrapers.uiauto import WinUIAutomationScraper

    scraper_address = "192.168.22.32"  # address of the scraper agent within the guest OS
    scraper_address = 8000             # port of the scraper agent within the guest OS

    scraper = WinUIAutomationScraper(scraper_address, scraper_port)

Lastly, the Windows Interpreter class is constructed using the above interfaces.

.. code:: python

    from murphy.model.interpreters.windows import WindowsInterpreter

    interpreter = WindowsInterpreter(feedback, control, scraper)

The Travel Journal
------------------

The Travel Journal provides useful information regarding the execution of the GUI application.

.. code:: python

    from murphy.journal import Journal

    journal_path = '.'  # local path where to store Journal information

    journal = Journal(journal_path)

Exploring the application
-------------------------

Once all the resources are initialized, the control can be handed over to the main loop which implements the application exploration logic. The logic can be summarised as follows:

1. Interpret the current visible state of the GUI application
2. Compare the given state with the known ones in the Journal
3. Select a new action to perform
4. Perform the action
5. Return to point #1

.. code:: python

    import time

    while True:
        new_state = interpreter.interpret_state()

        node = update_journal(new_state)

        action = choose_action()

        action.perform()

        time.sleep(3)

Once a new state is returned by the Interpreter, the logic compares it with the Journal content. The Journal will return an old node or a new one according to whether the new state was ever encountered before.

The `update_journal` function sets the new node as the current one and renders the Journal as an HTML page.

.. code:: python

    def update_journal(state):
        if state in journal:
            node = journal.find_node(state)
        else:
            node = journal.new_node(state)

        journal.current_node = node
        journal.render()

        return node

The application State the Node refers to can be accessed from its namesake attribute. The State encapsulates the available Actions which can be performed. In order to acknowledge whether the Action was already performed, a boolean attribute is appended to its instance.

The action to perform is randomly chosen among the ones which have not been performed yet.

.. code:: python

    import random

    def choose_action(node):
        actions = []

        for action in node.state.actions:
            if not hasattr(action, 'performed'):
                action.performed = False
                actions.append(action)
            elif not action.performed:
                actions.append(action)

        action = random.choose(actions)
        action.performed = True

        return action

Conclusions and references
--------------------------

The above implemented Agent is intended to be simple to give a complete yet easy to understand illustration of Mr. Murphy abstraction layers and their integration.

Several aspects such as the handling of errors and corner cases where purposedly omitted. This Agent implementation will wander aimlessly within a GUI application until it finds a State with no available Actions to perform and then it will crash.

More complete examples can be found in the folder `murphy/agents`.
