from vncdotool import api

from murphy.automation import MurphyFactory


class VNCFactory(MurphyFactory):
    """Factory class for vncdotools-based automation.

    :param server: server URL in the form: host:screen, host::port.

    """
    def __init__(self, server: str, password: str = None):
        self._client = None
        self._server = server
        self._password = password

    def __call__(self):
        if self._client is None:
            self._client = api.connect(self._server, password=self._password)
            self._client.timeout = 60

        return self._client
