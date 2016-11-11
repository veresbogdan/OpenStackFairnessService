from fairness.node.libvirt_driver import LibvirtConnection
from fairness.node.nri import NRI


class RUI(object):
    """ This class represents the RUI data model (resource utilizaton information) """

    server_greediness = {}

    def __init__(self):
        self.cpu_time = None
        self.memory_used = None
        self.disk_bytes_read = None
        self.disk_bytes_written = None
        self.network_bytes_received = None
        self.network_bytes_transmitted = None
        RUI._get_values(self)

    def _get_values(self):
        conn = LibvirtConnection()
        domainIDs = conn.get_domain_IDs()
        if len(domainIDs) == 0:
            print(' No VM in running state')
        else:
            for domainID in domainIDs:
                print " "
                print(' Domain ID: ' + str(domainID))
                conn.get_domain_info(domainID)
                self.cpu_time = conn.get_vcpu_stats(domainID)
                self.memory_used = conn.get_memory_stats(domainID)
                self.disk_bytes_read = conn.get_disk_stats(domainID)[0]
                self.disk_bytes_written = conn.get_disk_stats(domainID)[1]
                self.network_bytes_received = conn.get_network_stats(domainID)[0]
                self.network_bytes_transmitted = conn.get_network_stats(domainID)[1]
                # print "CPU time in sec: ", conn.get_vcpu_stats(domainID)
                # print "Memory usage (rss) in Bytes (incl. swap_in if available): ", conn.get_memory_stats(domainID)
                # print "Disk stats (read, write in bytes):", conn.get_disk_stats(domainID)
                # print "Network stats (read, write in bytes):", conn.get_network_stats(domainID)

    # TODO
    def get_vm_greediness(self):
        return 'TODO Greed ' + NRI._get_public_ip_address()
