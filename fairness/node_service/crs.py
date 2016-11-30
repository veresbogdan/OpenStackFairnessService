class CRS(object):

    def __init__(self):
        self._cpu = None
        self._memory = None
        self._disk_read = None
        self._disk_write = None
        self._network_rx = None
        self._network_tx = None

    @property
    def cpu(self):
        return self._cpu

    @cpu.setter
    def cpu(self, value):
        self._cpu = value

    @property
    def memory(self):
        return self._memory

    @memory.setter
    def memory(self, value):
        self._memory = value

    @property
    def disk_read(self):
        return self._disk_read

    @disk_read.setter
    def disk_read(self, value):
        self._disk_read = value

    @property
    def disk_write(self):
        return self._disk_write

    @disk_write.setter
    def disk_write(self, value):
        self._disk_write = value

    @property
    def network_rx(self):
        return self._network_rx

    @network_rx.setter
    def network_rx(self, value):
        self._network_rx = value

    @property
    def network_tx(self):
        return self._network_tx

    @network_tx.setter
    def network_tx(self, value):
        self._network_tx = value
