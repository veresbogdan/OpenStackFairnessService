import socket
from fairness.virtual_machine import VM

import numpy as np
from metrics import greediness_raw
from metrics import GreedinessParameters


class ThisNode:
    def __init__(self, cpu, bogo, ram, disk=1, net=1):
        """
        Store the node's physical resource/Node Resource Information (NRI)
        :param cpu: nri
        :param bogo: nri
        :param ram: nri
        :param disk: nri
        :param net: nri
        :return:
        """
        self.own_nri_dict = {'CPUs': cpu,
                             'bogo': bogo,  # does not occur in CRI vector
                             'bogoXcpus': cpu * bogo,
                             'RAM': ram,
                             'disk': disk,
                             'net': net,
                             'vec': np.array([cpu * bogo, ram, disk, net])
                             }
        # this_node.own_nri_vec = np.array([cpu*bogo, ram, disk, net])
        self.added_to_crs = False
        self.added_to_hvn = None
        self.crs_dict = None
        self.hvn_dict = None
        self.vms = dict()
        self.hostname = socket.gethostname()

    def update_endowments(self):
        """
        only needs to be called, when set of VMs changes
        :return:
        """

        vr_sum = np.zeros(len(self.own_nri_dict['vec']))
        for vm in self.vms:
            vr_sum += self.vms[vm].vrs

        relative_endow = self.own_nri_dict['vec'] / vr_sum
        for i in range(len(relative_endow)):
            if relative_endow[i] > 1:
                relative_endow[i] = 1

        for vm in self.vms:
            self.vms[vm].endowment = self.vms[vm].vrs  # * relative_endow

    # This has to be called for every VM before calling forward_hvn
    def add_vm(self, ident, owner, vcpus, vram):
        """
        :param ident: a string with the VM's unique identifier
        :param owner: a string with the VM's owner's unique identifier
        :param vcpus: an integer with the number of the VM's VCPUs
        :param vram: an integer with the amount of the VM's VRAM
        :return:
        """
        self.vms[ident] = VM(ident, owner, vcpus, vram)

    def remove_vm(self, ident):
        """
        Remove the VM from the dictionary with the node's VMs
        :param ident: a string with the VM's unique identifier
        :return:
        """
        del self.vms[ident]

    def update_vms_rui(self, idnt, cpu_time, ram, disk=0, net=0):
        self.vms[idnt].rui = np.array([cpu_time, ram, disk, net])

    def forward_crs(self, crs_dict):
        """
        # Call when receiving the crs_dict
        :param crs_dict:
        :return:
        """
        assert self.own_nri_dict is not None
        if self.added_to_crs:
            self.crs_dict = dict(crs_dict)
        else:
            self.added_to_crs = True
            for pr in crs_dict:
                crs_dict[pr] += self.own_nri_dict[pr]

    def forward_hvn(self, hvn_dict):
        """
        # Call when receiving the hvn_dict
        :param hvn_dict:
        :return:
        """
        if self.added_to_hvn is None:
            self.added_to_hvn = dict()
            for user in hvn_dict:
                self.added_to_hvn[user] = 0.

        self.hvn_dict = dict(hvn_dict)

        self.update_endowments()
        rui = np.empty([len(self.vms), 4])
        endowments = np.empty([len(self.vms), 4])

        names = list()
        vm_iter = 0
        for vm in self.vms:  # concatenate the endowments vector
            rui[vm_iter, :] = self.vms[vm].rui
            endowments[vm_iter, :] = self.vms[vm].endowment
            names.append(vm)
            vm_iter += 1

        print "ttt"
        print endowments
        print rui
        print (1. / self.crs_dict['vec'])

        greediness = \
            greediness_raw(endowments, rui, self.crs_dict['vec'], GreedinessParameters()) \
            + np.sum(self.crs_dict['vec'] * endowments, axis=1)
        # todo: how is CPU time measured?
        # todo: how to determine endowment of CPU usage
        # todo: are a node's overall bogomips the product of its bogomips and cores?
        print "greediness"
        print greediness

        for i in range(len(self.vms)):
            self.vms[names[i]].heaviness = greediness[i]

        for user in self.added_to_hvn:
            self.hvn_dict[user] -= self.added_to_hvn[user]
            self.added_to_hvn[user] = 0

        for vm in self.vms:
            self.hvn_dict[self.vms[vm].owner] += self.vms[vm].heaviness
            self.added_to_hvn[self.vms[vm].owner] = self.vms[vm].heaviness

        return self.hvn_dict

    def get_priority(self, ident, min, max):
        """
        After all VMs are update, this method returns a VM's priority for this round
        :param ident: a string with the VM's unique identifier
        :param min: an integer with the minimal priority to be returned (depends on the resource)
        :param max: an integer with the maximal priority to be returned (depends on the resource)
        :return: The VM's priority for this round
        """
        pass
