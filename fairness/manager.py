#    while NRI of some host in Nf is missing:
#       send own NRI to nodes of which NRI is missing
#    use NRIs to calculate CRS and normalization vector
#    every mu seconds:
#     collect RUI of all VMs hosted by ni
#     apply hv to collected RUI in order to calculate
#         heaviness of all VMs hosted by ni
#     send this heaviness set to all n element of Nf - {ni}
#     wait to receive heaviness set from all n element of Nf - {ni}
#     apply hu to calculate the heaviness of all u element of U
#     for every VM v hosted by ni :
#         set priorities of v on according to hv(v) and hu(o(v))
from fairness.nri import NRI
from fairness.libvirt_driver import Connection
import sys


def main():
    nri = NRI()
    print "CPU weighted by BogoMIPS: ", nri.cpu
    print "Memory size in kilobytes: ", nri.memory
    print "Disk read speed in bytes/s: ", nri.disk_io
    print "Theoretical network throughput in bytes/s: ", nri.network_io

    # print sys.platform


if __name__ == '__main__':
    main()
