import libvirt


class Connection:
    """This class represents the connection to libvirt"""
    def __init__(self):
        self.conn = None
        pass

    def connect(self):
        self.conn = libvirt.open('qemu:///system')
        if self.conn == None:
            print('Failed to open connection to qemu:///system')
            exit(1)

    def get_domain(self, domName):
        dom = self.conn.lookupByName(domName)
        if dom == None:
            print('Failed to find the domain ' + domName)
            exit(1)

        state, maxmem, mem, cpus, cput = dom.info()
        print('The state is ' + str(state))
        print('The max memory is ' + str(maxmem))
        print('The memory is ' + str(mem))
        print('The number of cpus is ' + str(cpus))
        print('The cpu time is ' + str(cput))

    def get_info(self):
        return self.conn.getInfo()

