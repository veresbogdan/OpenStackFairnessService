from __future__ import print_function

import json
import sys
import zmq

from fairness.config_parser import MyConfigParser
from fairness.node_service.nri import NRI
from fairness.node_service.rui import RUI
from fairness.openstack_driver import IdentityApiConnection
from fairness.node import Node
from fairness.virtual_machines import VM
from fairness.virtual_machines import quota_to_scalar


def get_successor_from_controller(socket, nri):
    print("sending...")
    json_message = json.dumps({'advertiser': Node.get_public_ip_address(), 'nri': nri})
    socket.send(json_message)

    print("waiting for response...")
    json_response = socket.recv()
    response = json.loads(json_response)
    ip = response['successor_ip']
    port = response['successor_port']
    own_port = response['requester_port']
    return ip, port, own_port


def main():
    config = MyConfigParser()
    controller_ip = config.config_section_map('keystone_authtoken')['controller_ip']

    nri = NRI()
    print("CPU weighted by BogoMIPS: ", nri.cpu)
    print("Host memory size in kilobytes: ", nri.memory)
    print("Disk read speed in bytes/s: ", nri.disk_read_bytes)
    print("Disk write speed in bytes/s: ", nri.disk_write_bytes)
    print("Theoretical network receive throughput in bytes/s: ", nri.network_receive)
    print("Theoretical network transmit throughput in bytes/s: ", nri.network_transmit)

    context = zmq.Context()
    #  Socket to talk to server
    client_socket = context.socket(zmq.REQ)
    print("Connecting to Controller...")
    address = "tcp://" + controller_ip + ":5555"
    client_socket.connect(address)

    # example of usage
    # sender = Sender()
    successor_ip, successor_port, own_port = get_successor_from_controller(client_socket, nri.__dict__)
    print("successor_ip: ", successor_ip)


    # Prepare broker sockets
    frontend = context.socket(zmq.ROUTER)
    backend = context.socket(zmq.DEALER)
    frontend.bind("tcp://*:" + own_port)
    print("frontend_port: ", own_port)
    backend_address = "tcp://" + successor_ip + ":" + successor_port
    print("backend_address: ", backend_address)
    backend.connect(backend_address)

    # Initialize broker poll set
    poller = zmq.Poller()
    poller.register(frontend, zmq.POLLIN)
    poller.register(backend, zmq.POLLIN)

    # Switch messages between sockets
    while 1:
        socks = dict(poller.poll())

        if socks.get(frontend) == zmq.POLLIN:
            message = frontend.recv_multipart()
            print("message: ", message)
            backend.send_multipart(message)

        if socks.get(backend) == zmq.POLLIN:
            message = backend.recv_multipart()
            frontend.send_multipart(message)




    # connect to OpenStack API
    open_stack_connection = IdentityApiConnection()
    user_dict = open_stack_connection.list_users()
    # user_dict = {"demo": 0, "admin": 0}
    cores, ram = open_stack_connection.get_quotas()
    vm_dict = open_stack_connection.get_vms(user_dict)
    print("vm_dict: ", vm_dict)

    # initialize user greediness with 0's.
    user_initial_greediness = {}
    for key, value in user_dict.items():
        user_initial_greediness[value] = 0
    print("user_initial_greediness: ", user_initial_greediness)
    # print("user_dict: ", user_dict)

    # TODO: from here on I need the complete CRS fom the controller
    crs = [11998, 4040944, 4040944000, 4040944000, 125000000, 125000000]

    # initialize node with 6 normalization factors and 6 resources.
    node = Node([1/crs[0], 1/crs[1], 1/crs[2], 1/crs[3], 1/crs[4], 1/crs[5]], [nri.cpu, nri.memory, nri.disk_read_bytes, nri.disk_write_bytes, nri.network_receive, nri.network_transmit], user_initial_greediness)
    print("Node initialized.")

    hostname = node.hostname

    domain_id_list_new = []
    for inst in vm_dict:
        if inst.values()[0][1] == hostname:
            domain_id_list_new.append(inst.keys()[0])
    print("domain_id_list_new: ", domain_id_list_new)

    rui = RUI()  # TODO: create new RUI for every VM.
    # domain_id_list = rui.get_domain_id_list()
    if domain_id_list_new is not None:
        for domain in domain_id_list_new:
            # print("")
            # print("Domain ID:", domain, "on host", hostname)
            max_mem, cpu_s = rui.get_vm_info(domain) # TODO: domains vms to get only those on local node.
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

    # Receiver(nri, rui)  # CRS and user greediness


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
