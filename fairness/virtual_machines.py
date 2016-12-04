import numpy as np
from fairness.node_service.rui import RUI

__author__ = 'Patrick'


class VM:

    def __init__(self, vm_id, vrs, owner, node):
        """
        :param vrs: sequence (list, np.array, etc.) that specifies the VM's VRs
        :param owner: string that specifies the VM's owner (must be key in the owner dictionary)
        """
        # assert len(vrs) == len(VM.nri)
        # assert owner in node.owners

        self.vm_id = vm_id
        self.vrs = np.array(vrs)
        self.owner = owner
        self.rui = None             # change to RUI()
        self.endowment = None
        node.vms.append(self)

    def update_rui(self, rui):
        """
        :param rui: the VM's RUI in the current measurement period
        """
        # assert len(rui) == len(VM.global_normalization)
        self.rui = np.array(rui)


# pro user ausrechnen auf jedem node
def quota_to_scalar(quota, node):
    """
    The quota given as input will be multiplied with the global normalization vector given to init() and the sum returned.
    :param quota: sequence (list, np.array, etc.) that specifies a user's quota. Must have same length as the global normalization vector
    :return: the number that needs to be deducted from a user's heaviness
    """
    assert len(quota) == len(node.global_normalization[:2])
    return sum(np.array(quota) * node.global_normalization[:2])
