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
                state, maxmem, mem, cpus, cput = conn.get_domain_info(domainID)
                print('The state is ' + str(state))
                print('The max memory is ' + str(maxmem))
                print('The memory is ' + str(mem))
                print('The number of vcpus is ' + str(cpus))
                print('The cpu time is ' + str(cput))

                conn.get_vcpu_stats(domainID)
                conn.get_ostype(domainID)
                conn.get_memory_stats(domainID)
