import time
from collections import namedtuple

from lxml import etree

from murphy.automation import LoadAverage, MurphyFactory


Measure = namedtuple('Measure', ('time', 'value'))


class VirtualboxLoad(LoadAverage):
    """VirtualboxLoad based implementation of LoadAverage."""
    def __init__(self, factory: MurphyFactory):
        self.disk_throughput = DISK_THROUGHPUT
        self.network_bandwidth = NETWORK_BANDWIDTH

        self._machine = factory()
        self._prev_cpu_measure = self._cpu_measure()
        self._prev_disk_measure = self._disk_measure()
        self._prev_network_measure = self._network_measure()

    @property
    def cpu(self) -> float:
        """CPU load as aggregated percentage of all VCPUs."""
        measure = self._cpu_measure()
        previous = self._prev_cpu_measure

        self._prev_cpu_measure = measure

        return measure_delta(measure, previous)

    @property
    def disk(self) -> float:
        """Disk IO activity as read + write bytes."""
        measure = self._disk_measure()
        previous = self._prev_disk_measure
        throughput = measure_delta(measure, previous)

        self._prev_disk_measure = measure

        if throughput > self.disk_throughput:
            self.disk_throughput = throughput

        return throughput / self.disk_throughput

    @property
    def network(self) -> float:
        """Network IO activity."""
        measure = self._network_measure()
        previous = self._prev_network_measure
        bandwidth = measure_delta(measure, previous)

        self._prev_network_measure = measure

        if bandwidth > self.network_bandwidth:
            self.network_bandwidth = bandwidth

        return bandwidth / self.network_bandwidth

    def _cpu_measure(self) -> Measure:
        cpus = self._machine.cpu_count

        with self._machine.create_session() as session:
            statistics = session.console.debugger
            output = statistics.get_stats('/TM/CPU*/cNsExecuting', False)

        tree = etree.fromstring(output.encode())
        cpu = sum(int(e.get('val')) for e in tree.xpath(CPU_XPATH))

        return Measure(time.time(), cpu / cpus / NANOSECOND)

    def _disk_measure(self) -> Measure:
        with self._machine.create_session() as session:
            statistics = session.console.debugger
            output = statistics.get_stats('/Devices/IDE*/*Bytes', False)

        tree = etree.fromstring(output.encode())
        disk = sum(int(e.get('c')) for e in tree.xpath(DISK_XPATH))

        return Measure(time.time(), disk)

    def _network_measure(self) -> Measure:
        with self._machine.create_session() as session:
            statistics = session.console.debugger
            output = statistics.get_stats('/Devices/*/TransmitBytes', False)
            tree = etree.fromstring(output.encode())
            transmit = sum(int(e.get('c')) for e in tree.xpath(NETWORK_XPATH))
            output = statistics.get_stats('/Devices/*/ReceiveBytes', False)
            tree = etree.fromstring(output.encode())
            receive = sum(int(e.get('c')) for e in tree.xpath(NETWORK_XPATH))

        return Measure(time.time(), transmit + receive)


def measure_delta(current, previous):
    return (current.value - previous.value) / (current.time - previous.time)


DISK_THROUGHPUT = 100
NETWORK_BANDWIDTH = 125000  # estimated on a 1Mb network connection
NANOSECOND = 1000000000.0
CPU_XPATH = ".//U64[starts-with(@name, '/TM/CPU/')]"
DISK_XPATH = ".//Counter[starts-with(@name, '/Devices/IDE')]"
NETWORK_XPATH = ".//Counter[starts-with(@name, '/Devices/')]"
