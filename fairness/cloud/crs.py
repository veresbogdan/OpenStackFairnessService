class CRS(object):

    def __init__(self):
        self._cpu_bogo = 0
        self._cpu_num = 0
        self._memory = 0
        self._disk_read = 0
        self._disk_write = 0
        self._network_rx = 0
        self._network_tx = 0
        self._hash_value = 0

    @property
    def cpu_bogo(self):
        return self._cpu_bogo

    @cpu_bogo.setter
    def cpu_bogo(self, value):
        self._cpu_bogo = value

    @property
    def cpu_num(self):
        return self._cpu_num

    @cpu_num.setter
    def cpu_num(self, value):
        self._cpu_num = value

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

    # the hash value is used by the nodes
    @property
    def hash_value(self):
        return self._hash_value

    @hash_value.setter
    def hash_value(self, value):
        self._hash_value = value

    def update_crs(self, new_nri):
        self._cpu_bogo += new_nri['cpu_bogo']
        self._cpu_num += new_nri['cpu_num']
        self._memory += new_nri['memory']
        self._disk_read += new_nri['disk_read_bytes']
        self._disk_write += new_nri['disk_write_bytes']
        self._network_rx += new_nri['network_receive']
        self._network_tx += new_nri['network_transmit']
