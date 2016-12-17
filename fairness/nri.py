import subprocess
import multiprocessing
import re
import os


class NRI(object):
    """ This class represents the NRI data model (node resource information) """

    MAX_NETWORK_THROUGHPUT = 1000
    server_crs = {}
    server_greediness = {}
    old_inverted_greed = {}

    def __init__(self):
        self.cpu = 1  # amount of CPU cores on the compute node, normalized by the node's BogoMIPS
        self.memory = 1  # total amount of installed memory in kilobytes
        self.disk_read_bytes = 1  # combined disk read speeds of all disks in bytes/s
        self.disk_write_bytes = 1  # combined disk write speeds of all disks in bytes/s
        self.network_receive = 1  # network receive throughput in bytes/s
        self.network_transmit = 1  # network transmit throughput in bytes/s
        NRI._get_values(self)

    def _get_values(self):
        """ Retrieve the values for NRI and fill the object fields.
        :return: None
        """
        self.cpu = NRI._get_cpu_count_weighted(self)
        self.memory = NRI._get_installed_memory()
        # self.disk_read_bytes = NRI._get_disk_read_speeds()
        # self.disk_write_bytes = NRI._get_disk_write_speeds()
        self.network_receive = NRI._get_network_receive_throughput(self)
        self.network_transmit = NRI._get_network_transmit_throughput(self)

    def _get_cpu_count_weighted(self):
        return multiprocessing.cpu_count() * self._get_bogomips()

    # _get_public_ip_address was moved to node.py

    @staticmethod
    def _get_bogomips():
        """ Get the BogoMIPS of the machine from /proc/cpuinfo

        BogoMIPS values are available for each core, so the average
        value is returned to get an overall rating of the host's performance.
        It is however important to note that BogoMIPS, as the name implies, is
        a completely unscientific measurement of host performance and is only
        used to get an approximate idea of the performance

        :return: BogoMIPS average of the host
        :rtype: int
        """
        bogomips = 1
        try:
            output = subprocess.check_output(['cat', '/proc/cpuinfo'])
            if output is not None:
                m = re.findall(r'bogomips\t:\s(\d+\.\d+)', output)
                if m is not None:
                    bogomips = 0
                    for value in m:
                        bogomips += float(value)
                    bogomips = int(bogomips / len(m))
        except subprocess.CalledProcessError:
            pass
        return bogomips

    @staticmethod
    def _get_installed_memory():
        """ Get the amount of installed memory in kilobytes

        :return: Installed memory in kilobytes
        :rtype: int
        """
        try:
            output = subprocess.check_output(['free', '-k'])
            if output is not None:
                memory = int(output.splitlines()[1].strip().split()[1])
                return memory
            return None
        except subprocess.CalledProcessError:
            pass
        return None

    @staticmethod
    def _get_disks():
        disks = list()
        try:
            output = subprocess.check_output(['lsblk', '-io', 'KNAME,TYPE'])
            if output is not None:
                for line in output.splitlines():
                    line_segments = line.split(' ')
                    if line_segments[len(line_segments) - 1] == 'disk':
                        disks.append(line_segments[0])
        except subprocess.CalledProcessError:
            print ("An error in _get_disks() has ocured: Command 'exit 1' returned non-zero exit status 1")
        return disks

    @staticmethod
    def _get_disk_read_speeds():
        """ Returns the sum of all disk read speeds in bytes/s. Every disk is
        tested 3 times.

        :return: Combined disk speeds in bytes/s
        :rtype: int
        """
        iterations = 3
        speeds = 0
        disks = NRI._get_disks()
        try:
            for disk in disks:
                inner_sum_speed = 0
                output = None
                for i in range(iterations):
                    output = subprocess.check_output(['sudo', 'hdparm', '-t', '/dev/' + disk])
                    if output is not None:
                        lines = output.splitlines()
                        line_segments = lines[2].split(' ')
                        speed_in_mbs = line_segments[len(line_segments) - 2]
                        speed_in_bytes = float(speed_in_mbs) * 1000000
                        inner_sum_speed += int(speed_in_bytes)
                if output is not None:
                    speeds += inner_sum_speed / iterations
        except subprocess.CalledProcessError:
            print ("An error in _get_disk_read_speeds() has ocured: Command 'exit 1' returned non-zero exit status 1")
        return speeds

    @staticmethod
    def _get_disk_write_speeds():
        iterations = 3
        speeds = 0
        disks = NRI._get_disks()
        try:
            for disk in disks:
                inner_sum_speed = 0
                err = None
                for i in range(iterations):
                    output, err = subprocess.Popen(['sudo', 'dd', 'if=/dev/' + disk, 'of=' + os.path.expanduser('~/disk_benchmark_file'), 'bs=8k', 'count=200k'], stderr=subprocess.PIPE).communicate()
                    subprocess.check_output(['sudo', 'rm', os.path.expanduser('~/disk_benchmark_file')])
                    if err is not None:
                        lines = err.splitlines()
                        line_segments = lines[2].split(' ')
                        speed_in_mbs = line_segments[len(line_segments) - 2]
                        speed_in_bytes = float(speed_in_mbs) * 1000000
                        inner_sum_speed += int(speed_in_bytes)
                if err is not None:
                    speeds += inner_sum_speed / iterations
        except subprocess.CalledProcessError:
            print ("An error in _get_disk_write_speeds() has ocured: Command 'exit 1' returned non-zero exit status 1")
        return speeds

    def _get_network_receive_throughput(self):
        """ return theoretical network throughput in bytes/s """
        return self.MAX_NETWORK_THROUGHPUT * 125000

    def _get_network_transmit_throughput(self):
        """ return theoretical network throughput in bytes/s """
        return self.MAX_NETWORK_THROUGHPUT * 125000
