from __future__ import print_function

import socket

import numpy as np

from fairness.cloud.metrics import greediness_raw, GreedinessParameters

__author__ = 'Patrick'


class Node(object):
    def __init__(self):
        """
        This class represents the Fairness Node that holds the VMs.
        """
        self.nri = None
        self.vms = list()
        self.global_normalization = [1, 1, 1, 1, 1, 1]
        self.hostname = socket.gethostname()
        self.public_ip = Node.get_public_ip_address()

    def set_nri(self, nri):
        """
        fills the nri NumPy array in the node class.
        :param nri: this is the NRI object
        :return: None
        """
        array_nri = [nri.cpu_bogo,
                     nri.memory,
                     nri.disk_read_bytes,
                     nri.disk_write_bytes,
                     nri.network_receive,
                     nri.network_transmit]
        self.nri = np.array(array_nri)

    def update_global_normalization(self, n_crs):
        """
        This function has to be calles every time the CRS has changed.
        :param n_crs: the new CRS vector.
        :return: None
        """
        gn_list = [1.0 / int(n_crs['cpu_bogo']), 1.0 / int(n_crs['memory']), 1.0 / int(n_crs['disk_read_bytes']), 1.0 / int(n_crs['disk_write_bytes']), 1.0 / int(n_crs['network_receive']), 1.0 / int(n_crs['network_transmit'])]
        # print("gn_list: ", gn_list)
        self.global_normalization = np.array(gn_list)

    def append_vm_and_update_endowments(self, new_vm):
        """
        This method only needs to be called, when a new VMs is created.
        :param new_vm: the VM object to add to the node.
        :return: None
        """
        self.vms.append(new_vm)
        vr_sum = np.zeros(2)

        for vm in self.vms:
            vr_sum += vm.vrs

        trimmed_nri = np.array(self.nri[:2])
        relative_endow = trimmed_nri / vr_sum
        for i in range(len(relative_endow)):
            if relative_endow[i] > 1:
                relative_endow[i] = 1

        for vm in self.vms:
            vm.endowment = vm.vrs * relative_endow

    def update_greediness_per_vm(self):
        """
        Updates the VMs' greediness and, therefore must be called after all RUI has been updated
        the greediness will be contained in the .heaviness attribute of the VM objects.
        The endowments were updated in the append_vm_and_update_endowments() method of this module.
        :return: None
        """

        rui = np.empty([len(self.vms), len(self.vms[0].rui[:2])])
        endowments = np.empty([len(self.vms), len(self.vms[0].endowment)])

        for i in range(len(self.vms)):  # concatenate the endowments vector
            rui[i, :] = self.vms[i].rui[:2]
            endowments[i, :] = self.vms[i].endowment

        greediness = \
            greediness_raw(endowments, rui, self.global_normalization[:2], GreedinessParameters()) \
            + np.sum(self.global_normalization[:2] * endowments, axis=1)

        for i in range(len(self.vms)):
            self.vms[i].heaviness = greediness[i]

    @staticmethod
    def get_public_ip_address():
        """
        helper function to get the own IP address.
        :return: public ip address of the host.
        """
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = (s.getsockname()[0])
        s.close()
        return ip

    def quota_to_scalar(self, quota):
        """
        This function is deprecated. It is only used in the vitural_machine_tester.py.
        The quota given as input will be multiplied with the global normalization vector
        and the sum is returned.
        :param quota: sequence (list, np.array, etc.) that specifies a user's quota.
        Must have same length as the global normalization vector
        :return: the number that needs to be deducted from a user's heaviness
        """
        assert len(quota) == len(self.global_normalization[:2])
        return sum(np.array(quota) * self.global_normalization[:2])
