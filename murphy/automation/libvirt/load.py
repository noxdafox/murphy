import time
from xml.etree import ElementTree
from collections import namedtuple

import libvirt

from murphy.automation import LoadAverage, MurphyFactory


Measure = namedtuple('Measure', ('time', 'value'))
DomainResources = namedtuple('DomainResources', ('cpus', 'disk', 'interface'))


class LibvirtLoad(LoadAverage):
    """Libvirt based implementation of LoadAverage."""
    def __init__(self, factory: MurphyFactory):
        self.disk_throughput = DISK_THROUGHPUT
        self.network_bandwidth = NETWORK_BANDWIDTH

        self._domain = factory()
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
        try:
            stats = self._domain.getCPUStats(True)[0]['cpu_time']
        except (libvirt.libvirtError, LookupError):
            raise RuntimeError("Unable to read CPU statistics")

        return Measure(time.time(), stats / self._resources.cpus / NANOSECOND)

    def _disk_measure(self) -> Measure:
        try:
            stats = self._domain.blockStats(self._resources.disk)
        except (libvirt.libvirtError, LookupError):
            raise RuntimeError("Unable to read Disk statistics")

        return Measure(time.time(), stats[1] + stats[3])

    def _network_measure(self) -> Measure:
        try:
            stats = self._domain.interfaceStats(self._resources.interface)
        except (libvirt.libvirtError, LookupError):
            raise RuntimeError("Unable to read Network statistics")

        return Measure(time.time(), stats[0] + stats[4])

    def _machine_resources(self) -> DomainResources:
        try:
            tree = ElementTree.fromstring(self._domain.XMLDesc())
        except libvirt.libvirtError:
            raise RuntimeError("Unable to retrieve VM description")

        cpus = int(tree.find('.//vcpu').text)
        disk_path = tree.find('.//disk[@type="file"]/source').get('file')
        interface = tree.find('.//devices/interface/target').get('dev')

        return DomainResources(cpus, disk_path, interface)


def measure_delta(current, previous):
    return (current.value - previous.value) / (current.time - previous.time)


DISK_THROUGHPUT = 100
NETWORK_BANDWIDTH = 125000  # estimated on a 1Mb network connection
NANOSECOND = 1000000000.0
