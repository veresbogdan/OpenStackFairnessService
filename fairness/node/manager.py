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

from __future__ import print_function
import sys
import socket
from fairness.virtual_machines import Node
from fairness.virtual_machines import VM
from fairness.node.nri import NRI
from fairness.node.rui import RUI
from fairness.node.openstack_driver import IdentityApiConnection


def main():
    nri = NRI()
    print("CPU weighted by BogoMIPS: ", nri.cpu)
    print("Host memory size in kilobytes: ", nri.memory)
    print("Disk read speed in bytes/s: ", nri.disk_io)
    print("Theoretical network throughput in bytes/s: ", nri.network_io)

    # connect to Openstack API
    open_stack_connection = IdentityApiConnection()
    user_dict = open_stack_connection.list_users()
    # open_stack_connection.list_projects()
    # open_stack_connection.get_quotas()

    # initialize node with 4 normalization factors and 4 resources.
    # TODO: where to get the normalization factors?? For the moment initialized to 1.
    Node.init([1, 1, 1, 1], [nri.cpu, nri.memory, nri.disk_io, nri.network_io], user_dict)
    print("Node initialized.")

    hostname = socket.gethostname()
    vm_list = []

    rui = RUI()
    domain_id_list = rui.get_domain_id_list()
    if domain_id_list is not None:
        for domain in domain_id_list:
            # print("")
            # print("Domain ID:", domain, "on host", hostname)
            maxmem, cpus = rui.get_vm_info(domain)
            rui.get_utilization(domain)
            # print("CPU time in sec: ", rui.cpu_time)
            # print("Memory usage (rss) in Bytes (incl. swap_in if available): ", rui.memory_used)
            # print("Disk stats (read in bytes):", rui.disk_bytes_read)
            # print("Disk stats (write in bytes):", rui.disk_bytes_written)
            # print("Network stats (read in bytes):", rui.disk_bytes_written)
            # print("Network stats (write in bytes):", rui.network_bytes_transmitted)

            vm = VM([maxmem, cpus], "demo")
            vm.update_rui(
                [rui.cpu_time, rui.memory_used, rui.disk_bytes_read, rui.disk_bytes_written, rui.disk_bytes_written,
                 rui.network_bytes_transmitted])
            vm_list.append(vm)
            # Node.update_endowments()

    for vm in vm_list:
        print(vm)
        print(vm.endowment)
        print(vm.global_normalization)
        print(vm.owner)
        print(vm.rui)







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
    sys.exit(main())
