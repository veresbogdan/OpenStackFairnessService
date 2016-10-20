from fairness.libvirt_driver import Connection

class RUI:
    """ This class represents the RUI data model (resource utilizaton information) """
    def __init__(self):
        self.cpu_time = None
        self.memory_used = None
        self.disk_bytes_read = None
        self.disk_bytes_written = None
        self.network_bytes_received = None
        self.network_bytes_transmitted = None

    def _get_values(self):
        conn = Connection()
        conn.connect()
        domain = conn.get_domain('instance-0000000a')
        print domain
