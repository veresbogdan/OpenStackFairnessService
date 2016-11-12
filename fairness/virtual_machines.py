__author__ = 'Patrick'

"""
This script will be used on every node
"""


from metrics import greediness_raw
import numpy as np
from metrics import GreedinessParameters


class Node(object):
    nri = None
    owners = None
    vms = list()

    def __init__(self):
        self.nri = None
        self.owners = None
        self.vms = list()

    @staticmethod
    def init(global_normalization, nri, owner_dictionary):
        """
        :param global_normalization: sequence (list, np.array, etc.) that specifies the cloud's global normalization vector
        :param nri: sequence (list, np.array, etc.) that describes the node's resources. must have same length as norm.
        :param owner_dictionary: python dict with owners unicodes
        :return:
        """
        assert isinstance(owner_dictionary, dict)
        assert len(global_normalization) == len(nri)
        VM.global_normalization = np.array(global_normalization)
        Node.nri = np.array(nri)
        Node.owners = owner_dictionary

    @staticmethod
    def update_endowments():
        """
        only needs to be called, when set of VMs changes
        :return:
        """

        vr_sum = np.zeros(2)

        for vm in Node.vms:
            vr_sum += vm.vrs

        relative_endow = Node.nri / vr_sum
        for i in range(len(relative_endow)):
            if relative_endow[i] > 1:
                relative_endow[i] = 1

        for vm in Node.vms:
            vm.endowment = vm.vrs * relative_endow


class VM:
    global_normalization = None
    # nri = None
    # owners = None
    # vms = list()

    def __init__(self, vrs, owner):
        """
        :param vrs: sequence (list, np.array, etc.) that specifies the VM's VRs
        :param owner: string that specifies the VM's owner (must be key in the owner dictionary)
        """
        # assert len(vrs) == len(VM.nri)
        # assert owner in VM.owners

        self.vrs = np.array(vrs)
        self.owner = owner
        self.rui = None
        self.endowment = None
        Node.vms.append(self)

    def update_rui(self, rui):
        """
        :param rui: the VM's RUI in the current measurement period
        """
        assert len(rui) == len(VM.global_normalization)
        self.rui = np.array(rui)


def get_greediness_per_user():
    """
    updates the VMs' greediness and, therefore must be called after all RUI has been updated
    the greediness will be contained in the .heaviness attribute of the VM objects
    :return:
    """

    rui = np.empty([len(Node.vms), len(Node.nri)])
    endowments = np.empty([len(Node.vms), len(Node.nri)])

    for i in range(len(Node.vms)):  # concatenate the endowments vector
        rui[i, :] = Node.vms[i].rui
        endowments[i, :] = Node.vms[i].endowment

    greediness =\
        greediness_raw(endowments, rui, VM.global_normalization, GreedinessParameters())\
        + np.sum(VM.global_normalization * endowments, axis=1)

    for i in range(len(Node.vms)):
        Node.vms[i].heaviness = greediness[i]


def quota_to_scalar(quota):
    """
    The quota given as input will be multiplied with the global normalization vector given to init() and the sum returned.
    :param quota: sequence (list, np.array, etc.) that specifies a user's quota. Must have same length as the global normalization vector
    :return: the number that needs to be deducted from a user's heaviness
    """
    assert len(quota) == len(VM.global_normalization)
    return sum(np.array(quota) * VM.global_normalization)
