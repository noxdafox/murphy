import time
import subprocess
from functools import reduce
from collections import namedtuple

from lxml import etree

from murphy.automation import LoadAverage, MurphyFactory


Measure = namedtuple('Measure', ('time', 'value'))
MachineResources = namedtuple('MachineResources', ('cpus'))
VBoxStatistics = namedtuple('VBoxStatistics', ('cpu', 'disk', 'network'))


class VirtualboxLoad(LoadAverage):
    """VirtualboxLoad based implementation of LoadAverage."""
    def __init__(self, factory: MurphyFactory):
        self.disk_throughput = DISK_THROUGHPUT
        self.network_bandwidth = NETWORK_BANDWIDTH

        self._machine_id = factory()
        self._prev_statistics = None
        self._resources = self._machine_resources()
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
        measure = vbox_statistics(self._machine_id, self._prev_statistics)

        return Measure(
            time.time(), measure.value.cpu / self._resources.cpus / NANOSECOND)

    def _disk_measure(self) -> Measure:
        measure = vbox_statistics(self._machine_id, self._prev_statistics)

        return Measure(time.time(), measure.value.disk)

    def _network_measure(self) -> Measure:
        measure = vbox_statistics(self._machine_id, self._prev_statistics)

        return Measure(time.time(), measure.value.network)

    def _machine_resources(self) -> MachineResources:
        command = (VBOX_MANAGER, 'showvminfo', self._machine_id)
        process = subprocess.Popen(
            command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        output = process.communicate(timeout=TIMEOUT)[0].decode()

        for line in output.splitlines():
            if line.startswith('Number of CPUs'):
                return MachineResources(int(line.split()[-1]))

        raise RuntimeError(
            "Unable to find the number of CPUs for %s" % self._machine_id)


def vbox_statistics(machine: str, previous: Measure = None) -> Measure:
    """As VirtualBox statistics are gathered through subprocess,
    a small caching mechanism is provided.

    """
    now = time.time()

    if previous is None or now - previous.time > STATISTICS_PERIOD:
        statistics = collect_vbox_statistics(machine)

        return Measure(now, statistics)

    return previous


def collect_vbox_statistics(machine: str) -> VBoxStatistics:
    command = (VBOX_MANAGER, 'debugvm', machine, 'statistics')
    process = subprocess.Popen(
        command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)

    return parse_output(process.communicate(timeout=TIMEOUT)[0])


def parse_output(output: str) -> VBoxStatistics:
    cpu = 0
    tree = etree.fromstring(output)

    cpu = reduce(
        lambda x, y: x + y, (int(e.get('val')) for e in tree.xpath(CPU_XPATH)))

    disk = int(tree.xpath(DISK_READ_XPATH)[0].get('c'))
    disk += int(tree.xpath(DISK_WRITE_XPATH)[0].get('c'))

    network = int(tree.xpath(NET_READ_XPATH)[0].get('c'))
    network += int(tree.xpath(NET_WRITE_XPATH)[0].get('c'))

    return VBoxStatistics(cpu, disk, network)


def measure_delta(current, previous):
    return (current.value - previous.value) / (current.time - previous.time)


TIMEOUT = 3
STATISTICS_PERIOD = 1
CPU_XPATH = (".//U64[starts-with(@name, '/TM/CPU/')"
             " and contains(@name, '/cNsExecuting')]")
DISK_READ_XPATH = (".//Counter[starts-with(@name, '/Devices/IDE')"
                   " and contains(@name, '/ReadBytes')]")
DISK_WRITE_XPATH = (".//Counter[starts-with(@name, '/Devices/IDE')"
                    " and contains(@name, '/WrittenBytes')]")
NET_READ_XPATH = (".//Counter[starts-with(@name, '/Devices/')"
                  " and contains(@name, '/ReceiveBytes')]")
NET_WRITE_XPATH = (".//Counter[starts-with(@name, '/Devices/')"
                   " and contains(@name, '/TransmitBytes')]")
DISK_THROUGHPUT = 100
NETWORK_BANDWIDTH = 125000  # estimated on a 1Mb network connection
NANOSECOND = 1000000000.0
VBOX_MANAGER = os.getenv('VBOX_MANAGER', default='vboxmanage')
