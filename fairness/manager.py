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
from fairness.rui import RUI
from fairness.openstack_driver import OpenStackConnection


def main():
    nri = NRI()
    print "CPU weighted by BogoMIPS: ", nri.cpu
    print "Host memory size in kilobytes: ", nri.memory
    print "Disk read speed in bytes/s: ", nri.disk_io
    print "Theoretical network throughput in bytes/s: ", nri.network_io

    rui = RUI()
    rui._get_values()

    # connect to Openstack API
    open_stack_connection = OpenStackConnection()
    token = open_stack_connection.authenticate()
    print token

    open_stack_connection.list_users()



    # Routine 1:
    # Collect NRI on the current node
    # Send NRI to next node
    # Receive NRI from the last nodes in the ring
    # Do it on start up and check every X seconds if there was some change in the infrastructure
    # (e.g. new nodes or died nodes). If changes happened, re-do collecting and advertising procedure.

    # Routine 2:
    # Collect information about the VMs on the node.
    # Do it on start up and re-collect information every X seconds for the case that
    # there was some changes in the VMs

    # Routine 3:
    # Collect RUI of living VMs
    # Calculate node heavinesses
    # Send heaviness to the next node
    # Receive the heaviness vector of the last node in the ring
    # update heaviness vector with own heaviness

    # Routine 4:
    # Calculate user heavinesses
    # Map the heaviness to priorities

    # Routine 5:
    # Reallocate resources via libvirt


if __name__ == '__main__':
    main()
