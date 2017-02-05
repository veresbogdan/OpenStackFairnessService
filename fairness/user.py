import numpy as np


class User:
    def __init__(self, idnt, vcpu, vram, disk=1, netw=1):
        self.idnt = idnt
        self.vcpu = vcpu
        self.vram = vram
        self.disk = disk
        self.netw = netw
        self.quota = np.array([vcpu, vram, disk, netw])
