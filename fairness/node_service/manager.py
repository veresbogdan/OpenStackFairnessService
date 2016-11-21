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

import socket
import sys

from fairness.node_service.nri import NRI
from fairness.node_service.rui import RUI
from fairness.openstack_driver import IdentityApiConnection
from fairness.node import Node
from fairness.virtual_machines import VM
from fairness.virtual_machines import quota_to_scalar


def main():
    nri = NRI()
    print("CPU weighted by BogoMIPS: ", nri.cpu)
    print("Host memory size in kilobytes: ", nri.memory)
    print("Disk read speed in bytes/s: ", nri.disk_read_bytes)
    print("Disk write speed in bytes/s: ", nri.disk_write_bytes)
    print("Theoretical network receive throughput in bytes/s: ", nri.network_receive)
    print("Theoretical network transmit throughput in bytes/s: ", nri.network_transmit)

    # connect to Openstack API
    open_stack_connection = IdentityApiConnection()
    user_dict = open_stack_connection.list_users()
    # user_dict = {"demo": 0, "admin": 0}
    # open_stack_connection.list_projects()
    cores, ram = open_stack_connection.get_quotas()
    vm_dict = open_stack_connection.get_vms(user_dict)
    print("vm_dict: ", vm_dict)

    # initialize user greediness with 0's.
    user_initial_greediness = {}
    for key, value in user_dict.items():
        user_initial_greediness[value] = 0
    # print("new dict: ", user_initial_greediness)
    # print("user_dict: ", user_dict)

    # initialize node with 6 normalization factors and 6 resources.
    # TODO: where to get the normalization factors?? For the moment initialized to 1. From CRS (1 / anzahl ressource)
    node = Node([1, 1/nri.memory, 1, 1, 1, 1], [nri.cpu, nri.memory, nri.disk_read_bytes, nri.disk_write_bytes, nri.network_receive, nri.network_transmit], user_initial_greediness)
    print("Node initialized.")

    hostname = node.hostname

    domain_id_list_new = []
    for key in vm_dict:
        domain_id_list_new.extend(vm_dict[key])
    print("domain_id_list_new: ", domain_id_list_new)

    rui = RUI()
    # domain_id_list = rui.get_domain_id_list()
    if domain_id_list_new is not None:
        for domain in domain_id_list_new:
            # print("")
            # print("Domain ID:", domain, "on host", hostname)
            max_mem, cpu_s = rui.get_vm_info(domain)
            rui.get_utilization(domain)
            # print("CPU time in sec: ", rui.cpu_time)
            # print("Memory usage (rss) in Bytes (incl. swap_in if available): ", rui.memory_used)
            # print("Disk stats (read in bytes):", rui.disk_bytes_read)
            # print("Disk stats (write in bytes):", rui.disk_bytes_written)
            # print("Network stats (read in bytes):", rui.network_bytes_received)
            # print("Network stats (write in bytes):", rui.network_bytes_transmitted)

            domain_id = hostname + "-" + str(domain)
            vm = VM(domain_id, [max_mem, cpu_s], "demo", node)
            vm.update_rui(
                [rui.cpu_time, rui.memory_used, rui.disk_bytes_read, rui.disk_bytes_written, rui.network_bytes_received,
                 rui.network_bytes_transmitted])
            node.update_endowments()

    node.get_greediness_per_user()

    for vm in node.vms:
        print(" VM ID: ", vm.vm_id)
        print(vm.endowment)
        print(node.global_normalization)
        print(vm.owner)
        print(vm.rui)
        print("VM Heaviness: ", vm.heaviness)

    print("Quota to sclar: ", quota_to_scalar([cores, ram], node))


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
