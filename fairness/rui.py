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
        # conn.connect()
        domainIDs = conn.get_domain_IDs()
        if len(domainIDs) == 0:
            print(' No VM in running state')
        else:
            for domainID in domainIDs:
                print(' ' + str(domainID))
                conn.get_domain_info(domainID)
                print ""
                conn.get_vcpu_stats(domainID)
                conn.get_memory_stats(domainID)
                print " Network stats:"
                conn.get_network_stats(domainID)
                print " Disk stats:"
                conn.get_disk_stats(domainID)
