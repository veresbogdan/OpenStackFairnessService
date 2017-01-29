import numpy as np

from fairness.drivers.libvirt_driver import LibvirtConnection

__author__ = 'Patrick'


class VM:
    def __init__(self, vm_name, vrs, owner, rui_object):
        """
        :param vm_name: the name of the VM. For example 'instance-00000006'
        :param vrs: sequence (list, np.array, etc.) that specifies the VM's VRs
        :param owner: string that specifies the VM's owner (must be key in the owner dictionary)
        :param rui_object: the object with the RUI values.
        """
        # assert len(vrs) == len(VM.nri)
        # assert owner in node.owners

        self.vm_name = vm_name
        self.vrs = np.array(vrs)
        self.owner = owner
        self.rui = None  # change to RUI()???
        self.rui_obj = rui_object
        self.endowment = None
        self.heaviness = None
        self.last_priority = None

    def update_rui(self, rui_object, rui):
        """
        :param rui_object: the rui object
        :param rui: the VM's RUI in the current measurement period
        """
        # assert len(rui) == len(VM.global_normalization)
        self.rui_obj = rui_object
        self.rui = np.array(rui)


def get_vrs(domain_id):
    conn = LibvirtConnection()
    state, maxmem, cpus = conn.get_domain_info(domain_id)
    # print('The state:', state)
    # print('The max memory:', maxmem)
    # print('The number of vcpus:', cpus)
    return maxmem, cpus


# pro user ausrechnen auf jedem node
def quota_to_scalar(quota, node):
    """
    The quota given as input will be multiplied with the global normalization vector given to init() and the sum returned.
    :param quota: sequence (list, np.array, etc.) that specifies a user's quota. Must have same length as the global normalization vector
    :return: the number that needs to be deducted from a user's heaviness
    """
    assert len(quota) == len(node.global_normalization[:2])
    return sum(np.array(quota) * node.global_normalization[:2])
