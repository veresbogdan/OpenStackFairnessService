import libvirt


class Connection:
    """This class represents the connection to libvirt"""
    def __init__(self):
        self.conn = libvirt.open('qemu:///system')
        if self.conn == None:
            print('Failed to open connection to qemu:///system')
            exit(1)

    def get_domain_IDs(self):
        domainIDs = self.conn.listDomainsID()
        if domainIDs == None:
            print('Failed to get a list of domain IDs')
        return domainIDs

    def get_domain_info(self, domainID):
        dom = Connection.domain_lookup(self, domainID)
        return dom.info()

    def get_info(self):
        return self.conn.getInfo()

    def get_ostype(self, domainID):
        dom = Connection.domain_lookup(self, domainID)
        type = dom.OSType()
        print('The OS type of the domain is: ' + type)

    def domain_lookup(self, domainID):
        dom = self.conn.lookupByID(domainID)
        if dom == None:
            print('Failed to find the domain ' + domainID)
            exit(1)
        return dom

    def get_vcpu_stats(self, domainID):
        dom = self.conn.lookupByID(domainID)
        print "CPU stat in nanoseconds: ", dom.getCPUStats(True)



