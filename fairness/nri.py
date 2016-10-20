import subprocess
import multiprocessing
import re


class NRI:
    """ This class represents the NRI data model (node resource information) """

    MAX_NETWORK_THROUGHPUT = 1000

    def __init__(self):
        self.cpu = None         # amount of CPU cores on the compute node, normalized by the node's BogoMIPS
        self.memory = None      # total amount of installed memory in kilobytes
        self.disk_io = None     # combined disk read speeds of all disks in bytes/s
        self.network_io = None  # network throughput in bytes/s
        NRI._get_values(self)

    def _get_values(self):
        # conn = Connection()
        # conn.connect()
        # node_info = conn.get_info()
        # print node_info
        # self.cpu = node_info[2]
        self.cpu = NRI._get_cpu_count_weighted(self)
        self.memory = NRI._get_installed_memory()
        self.disk_io = NRI._get_disk_speeds()
        self.network_io = NRI._get_network_throughput(self)

    def _get_cpu_count_weighted(self):
        return multiprocessing.cpu_count() * self._get_bogomips()

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
    def _get_disk_speeds():
        """ Returns the sum of all disk speeds in bytes/s. Every disk is
        tested 3 times.

        :return: Combined disk speeds in bytes/s
        :rtype: int
        """
        iterations = 3
        speeds = 0
        try:
            disks = list()
            output = subprocess.check_output(['lsblk', '-io', 'KNAME,TYPE'])
            if output is not None:
                for line in output.splitlines():
                    line_segments = line.split(' ')
                    if line_segments[len(line_segments) - 1] == 'disk':
                        disks.append(line_segments[0])
            for disk in disks:
                inner_sum_speed = 0
                for i in range(iterations):
                    output = subprocess.check_output(['sudo', 'hdparm', '-t', '/dev/' + disk])
                    # From man hdparm:
                    # -t	Perform  timings  of  device  reads  for benchmark and comparison purposes.
                    # For meaningful results, this operation should be repeated 2-3 times on an
                    # otherwise inactive system (no other active processes) with at least a couple
                    # of megabytes of free memory.  This displays the speed of reading through the
                    # buffer cache to the disk without any prior caching  of  data.
                    # This measurement  is  an indication of how fast the drive can sustain sequential
                    # data reads under Linux, without any filesystem overhead.
                    # To ensure accurate measurements, the buffer cache is flushed during the
                    # processing of -t using the BLKFLSBUF ioctl.
                    if output is not None:
                        lines = output.splitlines()
                        line_segments = lines[2].split(' ')
                        speed_in_mbs = line_segments[len(line_segments) - 2]
                        speed_in_bytes = float(speed_in_mbs) * 1000000
                        inner_sum_speed += int(speed_in_bytes)

                if output is not None:
                    speeds += inner_sum_speed / iterations

        except subprocess.CalledProcessError:
            print "An error in _get_disk_speeds() has ocured: Command 'exit 1' returned non-zero exit status 1"
        return speeds

    def _get_network_throughput(self):
        """ return theoretical network throughput in bytes/s """
        return self.MAX_NETWORK_THROUGHPUT * 125000
