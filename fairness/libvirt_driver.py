import libvirt


class Connection:
    """This class represents the connection to libvirt"""
    def __init__(self):
        self.conn = None
        pass

    def connect(self):
        self.conn = libvirt.open('qemu:///system')

    def get_info(self):
        return self.conn.getInfo()
