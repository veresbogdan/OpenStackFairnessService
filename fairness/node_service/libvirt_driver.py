from __future__ import print_function
import libvirt
from xml.etree import ElementTree


class LibvirtConnection(object):
    """This class represents the connection to libvirt"""

    def __init__(self):
        self.conn = libvirt.open('qemu:///system')
        if self.conn is None:
            print('Failed to open connection to qemu:///system')
            exit(1)

    # def get_domain_ids(self):
    #     domain_ids = self.conn.listDomainsID()
    #     if domain_ids is None:
    #         print('Failed to get a list of domain IDs')
    #     return domain_ids

    # for VM infos
    def get_domain_info(self, domain_name):
        dom = LibvirtConnection.domain_lookup(self, domain_name)
        state, maxmem, mem, cpus, cput = dom.info()
        return state, maxmem, cpus

    def domain_lookup(self, domain_name):
        dom = self.conn.lookupByName(domain_name)
        if dom is None:
            print('Failed to find the domain ', domain_name)
            exit(1)
        return dom

    # for RUI
    def get_vcpu_stats(self, domain_name):
        dom = self.conn.lookupByName(domain_name)
        # print "CPU stat in nanoseconds: ", dom.getCPUStats(True)
        cpu_time_seconds = (dom.getCPUStats(True)[0]['cpu_time']) / 1000000000.0
        return cpu_time_seconds

    def get_memory_stats(self, domain_name):
        dom = self.conn.lookupByName(domain_name)
        print("Memory stats in Byte: ", dom.memoryStats())
        memory_stats = dom.memoryStats()
        swap_in = None
        if 'swap_in' in memory_stats:
            swap_in = memory_stats['swap_in']
        rss = memory_stats['rss']
        if swap_in is not None:
            return swap_in + rss
        else:
            return rss

    def get_network_stats(self, domain_name):
        dom = self.conn.lookupByName(domain_name)
        tree = ElementTree.fromstring(dom.XMLDesc())
        iface = tree.find('devices/interface/target').get('dev')
        stats = dom.interfaceStats(iface)
        return stats[0], stats[4]

    def get_disk_stats(self, domain_name):
        dom = self.conn.lookupByName(domain_name)
        tree = ElementTree.fromstring(dom.XMLDesc())
        device = tree.find('devices/disk/target').get('dev')
        rd_req, rd_bytes, wr_req, wr_bytes, err = dom.blockStats(device)
        return rd_bytes, wr_bytes, rd_req, wr_req
