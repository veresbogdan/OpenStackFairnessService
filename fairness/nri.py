from fairness.libvirt_driver import Connection
import subprocess


class NRI:
    """ This class represents the NRI data model (node resource information) """
    def __init__(self):
        self.cpu = None         # amount of CPU cores on the compute node, normalized by the node's BogoMIPS
        self.memory = None      # total amount of installed memory in kilobytes
        self.disk_io = None     # combined disk read speeds of all disks in bytes/s
        self.network_io = None  # network throughput in bytes/s
        NRI._get_values(self)

    def _get_values(self):
        conn = Connection()
        conn.connect()
        node_info = conn.get_info()
        # print node_info
        self.cpu = node_info[2]
        self.memory = NRI._get_installed_memory(self)
        self.disk_io = NRI._get_disk_speeds(self)

    def _get_disk_speeds(self):
        """ Returns the sum of all disk speeds in bytes/s

        :return: Combined disk speeds in bytes/s
        :rtype: int
        """
        speeds = 0
        try:
            disks = list()
            output = subprocess.check_output(['lsblk', '-io', 'KNAME,TYPE'])
            # print output
            if output is not None:
                for line in output.splitlines():
                    line_segments = line.split(' ')
                    if line_segments[len(line_segments) - 1] == 'disk':
                        disks.append(line_segments[0])
            for disk in disks:
                output = subprocess.check_output(['sudo', 'hdparm', '-t', '/dev/' + disk])
                # print output
                if output is not None:
                    lines = output.splitlines()
                    line_segments = lines[2].split(' ')
                    speed_in_mbs = line_segments[len(line_segments) - 2]
                    speed_in_bytes = float(speed_in_mbs) * 1000000
                    speeds += int(speed_in_bytes)
        except subprocess.CalledProcessError:
            print "An error in _get_disk_speeds() has ocured: Command 'exit 1' returned non-zero exit status 1"
        print "speeds: ", speeds
        return speeds

    def _get_installed_memory(self):
        """ Get the amount of installed memory in kilobytes

        :return: Installed memory in kilobytes
        :rtype: int
        """
        try:
            output = subprocess.check_output(['free', '-k'])
            if output is not None:
                memory = int(output.splitlines()[1].strip().split()[1])
                print memory
                return memory
            return None
        except subprocess.CalledProcessError:
            pass
        return None
