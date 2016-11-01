import libvirt
from xml.etree import ElementTree


class Connection(object):
    """This class represents the connection to libvirt"""

    def __init__(self):
        self.conn = libvirt.open('qemu:///system')
        if self.conn is None:
            print('Failed to open connection to qemu:///system')
            exit(1)

    def get_domain_IDs(self):
        domainIDs = self.conn.listDomainsID()
        if domainIDs == None:
            print('Failed to get a list of domain IDs')
        return domainIDs

    # for VM infos
    def get_domain_info(self, domainID):
        dom = Connection.domain_lookup(self, domainID)
        state, maxmem, mem, cpus, cput = dom.info()
        print('The state is ' + str(state))
        print('The max memory is ' + str(maxmem))
        print('The memory is ' + str(mem))
        print('The number of vcpus is ' + str(cpus))
        print('The cpu time is ' + str(cput))

    def domain_lookup(self, domainID):
        dom = self.conn.lookupByID(domainID)
        if dom == None:
            print('Failed to find the domain ' + domainID)
            exit(1)
        return dom

    # for RUI
    def get_vcpu_stats(self, domainID):
        dom = self.conn.lookupByID(domainID)
        print "CPU stat in nanoseconds: ", dom.getCPUStats(True)

    def get_memory_stats(self, domainID):
        dom = self.conn.lookupByID(domainID)
        print "Memory stats: ", dom.memoryStats()

    def get_network_stats(self, domainID):
        dom = self.conn.lookupByID(domainID)
        tree = ElementTree.fromstring(dom.XMLDesc())
        iface = tree.find('devices/interface/target').get('dev')
        stats = dom.interfaceStats(iface)
        print('read bytes: ' + str(stats[0]))
        print('read packets: ' + str(stats[1]))
        print('read errors: ' + str(stats[2]))
        print('read drops: ' + str(stats[3]))
        print('write bytes: ' + str(stats[4]))
        print('write packets: ' + str(stats[5]))
        print('write errors: ' + str(stats[6]))
        print('write drops: ' + str(stats[7]))

    def get_disk_stats(self, domainID):
        dom = self.conn.lookupByID(domainID)
        tree = ElementTree.fromstring(dom.XMLDesc())
        device = tree.find('devices/disk/target').get('dev')
        rd_req, rd_bytes, wr_req, wr_bytes, err = dom.blockStats(device)
        print('Read requests issued: ' + str(rd_req))
        print('Bytes read: ' + str(rd_bytes))
        print('Write requests issued: ' + str(wr_req))
        print('Bytes written: ' + str(wr_bytes))
        print('Number of errors: ' + str(err))
