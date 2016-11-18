from __future__ import print_function
from fairness.node.libvirt_driver import LibvirtConnection
from fairness.node.nri import NRI


class RUI(object):
    """ This class represents the RUI data model (resource utilization information) """

    server_greediness = {}

    def __init__(self):
        self.cpu_time = None
        self.memory_used = None
        self.disk_bytes_read = None
        self.disk_bytes_written = None
        self.network_bytes_received = None
        self.network_bytes_transmitted = None

    @staticmethod
    def get_domain_id_list():
        conn = LibvirtConnection()
        domain_id_list = conn.get_domain_ids()
        if len(domain_id_list) == 0:
            print(' No VM in running state')
        else:
            return domain_id_list

    @staticmethod
    def get_vm_info(domain_id):
        conn = LibvirtConnection()
        state, maxmem, cpus= conn.get_domain_info(domain_id)
        print('The state:', state)
        print('The max memory:', maxmem)
        print('The number of vcpus:', cpus)
        return maxmem, cpus

    def get_utilization(self, domain_id):
        conn = LibvirtConnection()
        self.cpu_time = conn.get_vcpu_stats(domain_id)
        self.memory_used = conn.get_memory_stats(domain_id)
        self.disk_bytes_read = conn.get_disk_stats(domain_id)[0]  # 2 for IOPS
        self.disk_bytes_written = conn.get_disk_stats(domain_id)[1]  # 3 for IOPS
        self.network_bytes_received = conn.get_network_stats(domain_id)[0]
        self.network_bytes_transmitted = conn.get_network_stats(domain_id)[1]

    # TODO
    def get_vm_greediness(self):
        return 'TODO Greed ' + NRI._get_public_ip_address()
