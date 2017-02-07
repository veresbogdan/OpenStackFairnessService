import numpy as np


class VM:
    """This class is used internally only"""
    def __init__(self, ident, owner, vcpus, vram, disk=1, net=1):
        """
        Instantiate a VM object
        :param ident: a string with the VM's unique identifier
        :param owner: a string with the VM's owner's unique identifier
        :param vcpus: an integer with the number of the VM's VCPUs
        :param vram: an integer with the amount of the VM's VRAM
        :return:
        """
        self.ident = ident
        self.owner = owner

        self.vcpus = vcpus
        self.vram = vram
        self.vrs = np.array([vcpus, vram, disk, net])

        self.rui = None
        self.endowment = None
        self.heaviness = None

    # add the VM to the dictionary with the node's VMs
    def update_rui(self, cpu_time, ram, disk=0, net=0):
        """
        Update the resources the VM consumed
        :param cpu_time: CPU time in seconds utilized by the VM
        :param ram: RAM in KB utilized by the VM
        :param disk: Disk IO in ?? utilized by the VM
        :param net: Sum of traffic in ?? send and received by the VM
        """
        #assert len(rui) == len(VM.nri)
        self.rui = np.array([cpu_time, ram, disk, net])
