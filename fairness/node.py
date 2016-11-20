import socket

import numpy as np

__author__ = 'Patrick'


from fairness.metrics import greediness_raw, GreedinessParameters


class Node(object):

    def __init__(self, global_normalization, nri, owner_dictionary):
        """
        :param global_normalization: sequence (list, np.array, etc.) that specifies the cloud's global normalization vector
        :param nri: sequence (list, np.array, etc.) that describes the node's resources. must have same length as norm.
        :param owner_dictionary: python dict with owners unicodes
        :return:
        """
        self.nri = np.array(nri)
        self.owners = owner_dictionary
        self.vms = list()
        self.global_normalization = np.array(global_normalization)
        self.hostname = socket.gethostname()

    def update_endowments(self):
        """
        only needs to be called, when set of VMs changes
        :return:
        """

        vr_sum = np.zeros(2)

        for vm in self.vms:
            vr_sum += vm.vrs

        trimmed_nri = self.nri[:2]
        relative_endow = trimmed_nri / vr_sum
        for i in range(len(relative_endow)):
            if relative_endow[i] > 1:
                relative_endow[i] = 1

        for vm in self.vms:
            vm.endowment = vm.vrs * relative_endow

    def get_greediness_per_user(self):
        """
        updates the VMs' greediness and, therefore must be called after all RUI has been updated
        the greediness will be contained in the .heaviness attribute of the VM objects
        :return:
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