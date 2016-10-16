from fairness.libvirt_driver import Connection


class NRI:
    """ This class represents the NRI data model """
    def __init__(self):
        self.cpu = None         # amount of CPU cores on the compute node, normalized by the node's BogoMIPS
        self.memory = None      # total amount of installed memory in kilobytes
        self.disk_io = None     # combined disk read speeds of all disks in bytes/s
        self.network_io = None  # network throughput in bytes/s
        NRI._get_values(self)

    def _get_values(self):
        conn = Connection()
        conn.connect()
        node_info = conn.get_info()
        # print node_info
        self.cpu = node_info[2]
        self.memory = node_info[1]
