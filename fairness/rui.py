from __future__ import print_function

from datetime import datetime

from fairness.libvirt_driver import LibvirtConnection


class RUI(object):
    """ This class represents the RUI data model (resource utilization information) """

    server_greediness = {}

    def __init__(self):
        self.cpu_time = 0
        self.memory_used = 0
        self.disk_bytes_read = 0
        self.disk_bytes_written = 0
        self.network_bytes_received = 0
        self.network_bytes_transmitted = 0
        self.time_stamp = datetime.now()

    def get_utilization(self, domain_id):

        # memorizing the values of the last period
        last_cpu_time = self.cpu_time
        # last_memory_used = self.memory_used
        last_disk_bytes_read = self.disk_bytes_read
        last_disk_bytes_written = self.disk_bytes_written
        last_network_bytes_rx = self.network_bytes_received
        last_network_bytes_tx = self.network_bytes_transmitted
        last_time_stamp = self.time_stamp

        # retrieving the new values and calculating difference.
        conn = LibvirtConnection()

        # difference in cpu time used.
        self.cpu_time = conn.get_vcpu_stats(domain_id)
        cpu_time = self.cpu_time - last_cpu_time

        # get the current memory in use.
        memory_used = conn.get_memory_stats(domain_id)

        self.disk_bytes_read = conn.get_disk_stats(domain_id)[0] - self.disk_bytes_read  # 2 for IOPS
        disk_bytes_read = self.disk_bytes_read - last_disk_bytes_read
        print(self.disk_bytes_read)
        print(last_disk_bytes_read)
        print("disk_bytes_read: ", disk_bytes_read)


        self.disk_bytes_written = conn.get_disk_stats(domain_id)[1] - self.disk_bytes_written  # 3 for IOPS
        disk_bytes_written = self.disk_bytes_written - last_disk_bytes_written
        self.network_bytes_received = conn.get_network_stats(domain_id)[0] - self.network_bytes_received
        network_bytes_rx = self.network_bytes_received - last_network_bytes_rx
        self.network_bytes_transmitted = conn.get_network_stats(domain_id)[1] - self.network_bytes_transmitted
        network_bytes_tx = self.network_bytes_transmitted - last_network_bytes_tx
        self.time_stamp = datetime.now()
        # print("last_time_stamp: ", last_time_stamp)
        time_lapse = self.time_stamp - last_time_stamp
        # print("time_lapse: ", time_lapse)

        return [cpu_time, memory_used, disk_bytes_read, disk_bytes_written, network_bytes_rx, network_bytes_tx, time_lapse]
