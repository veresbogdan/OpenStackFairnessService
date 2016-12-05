from __future__ import print_function
import numpy as np
from fairness.node_service.libvirt_driver import LibvirtConnection
from fairness.node_service.rui import RUI

__author__ = 'Patrick'


class VM:

    def __init__(self, vm_name, vrs, owner):
        """
        :param vrs: sequence (list, np.array, etc.) that specifies the VM's VRs
        :param owner: string that specifies the VM's owner (must be key in the owner dictionary)
        :param node: this is the node object created in a prior step
        """
        # assert len(vrs) == len(VM.nri)
        # assert owner in node.owners

        self.vm_name = vm_name
        self.vrs = np.array(vrs)
        self.owner = owner
        self.rui = None             # change to RUI()
        self.endowment = None
        self.heaviness = None

    def update_rui(self, rui):
        """
        :param rui: the VM's RUI in the current measurement period
        """
        # assert len(rui) == len(VM.global_normalization)
        self.rui = np.array(rui)


def get_vrs(domain_id):
    conn = LibvirtConnection()
    state, maxmem, cpus = conn.get_domain_info(domain_id)
    # print('The state:', state)
    # print('The max memory:', maxmem)
    # print('The number of vcpus:', cpus)
    return maxmem, cpus