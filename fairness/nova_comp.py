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
                             'vec': list(np.array([cpu * bogo, ram, disk, net]))
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

        for i in range(len(self.own_nri_dict['vec'])):
            if vr_sum[i] == 0:
                vr_sum[i] = 1

        # create new resource vector, where CPUs are not scaled by the bogoMips
        temp = np.array(self.own_nri_dict['vec'])
        temp[0] = self.own_nri_dict['CPUs']

        relative_endow = temp/vr_sum
        for i in range(len(relative_endow)):
            if relative_endow[i] > 1:
                relative_endow[i] = 1
        # after setting each relative endowment to at most 1, scale the CPU endowment by
        relative_endow[0] *= self.own_nri_dict['bogo']

        for vm in self.vms:
            self.vms[vm].endowment = self.vms[vm].vrs * relative_endow

    # This has to be called for every VM before calling forward_hvn
    def add_vm(self, ident, owner, vcpus, vram, disk=1, net=1):
        """
        This has to be called for every VM (on the node) before calling forward_hvn
        :param ident: a string with the VM's unique identifier
        :param owner: a string with the VM's owner's unique identifier
        :param vcpus: an integer with the number of the VM's VCPUs
        :param vram: an integer with the amount of the VM's VRAM
        :return:
        """
        self.vms[ident] = VM(ident, owner, vcpus, vram, disk, net)
        self.update_endowments()

    def remove_vm(self, ident):
        """
        Remove the VM from the dictionary with the node's VMs
        :param ident: a string with the VM's unique identifier
        :return:
        """
        del self.vms[ident]
        self.update_endowments()

    def update_vms_rui(self, idnt, cpu_time, ram, disk=0, net=0):
        self.vms[idnt].rui = np.array([cpu_time, ram, disk, net])

    def forward_crs(self, crs_dict):
        """
        # Call when receiving the crs_dict
        :param crs_dict:
        :return:
        """
        self.crs_dict = dict(crs_dict)

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

        if len(self.vms) != 0:
            rui = np.empty([len(self.vms), 4])
            endowments = np.empty([len(self.vms), 4])

            # use names to ensure that rui and endowment vectors are iterated over in the same order as vms dict
            names = list()
            vm_iter = 0
            for vm in self.vms:  # concatenate the endowments vector
                rui[vm_iter, :] = self.vms[vm].rui
                endowments[vm_iter, :] = self.vms[vm].endowment
                names.append(vm)
                vm_iter += 1

            greediness =\
                greediness_raw(endowments, rui, self.crs_dict['vec'], GreedinessParameters(0.))\
                + np.sum(self.crs_dict['vec'] * endowments, axis=1)
            # todo: how is CPU time measured?
            # todo: how to determine endowment of CPU usage
            # todo: are a node's overall bogomips the product of its bogomips and cores?

            for i in range(len(self.vms)):
                self.vms[names[i]].heaviness = greediness[i]

            # Subtract from recived dictionary, what was added in the last round
            for user in self.added_to_hvn:
                self.hvn_dict[user] -= self.added_to_hvn[user]
                self.added_to_hvn[user] = 0

            # add current values to received dictionary and saves these to be subtracted in the next round
            for vm in self.vms:
                self.hvn_dict[self.vms[vm].owner] += self.vms[vm].heaviness
                self.added_to_hvn[self.vms[vm].owner] += self.vms[vm].heaviness

        return self.hvn_dict

    def get_priority(self, name, min_priority, max_priority):
        """
        After all VMs are update, this method returns a VM's priority for this round
        :param name: a string with the VM's or user's unique identifier
        :param min_priority: an integer with the minimal priority to be returned (depends on the resource)
        :param max_priority: an integer with the maximal priority to be returned (depends on the resource)
        :return: The VM's priority for this round
        """
        if name in self.vms:
            value = self.vms[name]
        elif name in self.hvn_dict:
            value = self.hvn_dict[name]
        else:
            raise LookupError("get_priority error: name neither found in vm dict nor user dict")
        max_expected = 1
        min_expected = -1
        if value <= min_expected:
            return min_priority
        if value >= max_expected:
            return max_priority
        return (value - min_expected) * (max_priority - min_priority) / (max_expected - min_expected) + min_priority
