from __future__ import print_function

import json
import yaml
import sys
import zmq

from fairness.config_parser import MyConfigParser
from fairness.node import Node
from fairness.node_service.nri import NRI
from fairness.node_service.rui import RUI
from fairness.node_service.crs import CRS
from fairness.openstack_driver import IdentityApiConnection
from fairness.virtual_machines import VM

crs = CRS()
node = Node()


def main():
    global node
    config = MyConfigParser()
    controller_ip = config.config_section_map('keystone_authtoken')['controller_ip']

    nri = NRI()
    node.set_nri(nri)
    print("CPU weighted by BogoMIPS: ", nri.cpu)
    # print("Host memory size in kilobytes: ", nri.memory)
    print("Disk read speed in bytes/s: ", nri.disk_read_bytes)
    # print("Disk write speed in bytes/s: ", nri.disk_write_bytes)
    # print("Theoretical network receive throughput in bytes/s: ", nri.network_receive)
    # print("Theoretical network transmit throughput in bytes/s: ", nri.network_transmit)

    context = zmq.Context()
    # create Socket to talk to server
    client_socket = context.socket(zmq.REQ)
    print("Connecting to Controller...")
    address = "tcp://" + controller_ip + ":5555"
    client_socket.connect(address)

    # send NRI and get info from Controller
    successor_ip, successor_port, own_port = get_successor_from_controller(client_socket, nri.__dict__)

    # TODO: create VMs and initialize RUI
    # still needed for VMs: VM ID, VRs, owner, node
    open_stack_connection = IdentityApiConnection()
    user_dict = open_stack_connection.list_users()
    # print("user_dict: ", user_dict)
    # user_dict:  {'4a6383e2a52f434386b2774ae8fe82ac': 'demo', 'bb097255bd524eb59debe189cbb0bd55': 'admin', 'bc39f112d92943bbbde80773ee01c1f1': 'glance', 'e6a534d6987048d8ab30fea4f7f34ca5': 'fairness', 'f387bb59a1454458b4ff8f82d9e51f7a': 'neutron', 'd928bbdff12d45d097ba58fdb90bac3c': 'nova'}
    vms_dict = open_stack_connection.get_all_vms(user_dict)
    # print("vms_dict: ", vms_dict)
    # vm_dict:  [{'instance-00000006': ('demo', 'n01')}, {'instance-00000005': ('demo', 'n02')}]

    # filter VMs that are on this host.
    vms_on_this_host = []
    hostname = node.hostname
    for inst in vms_dict:
        if inst.values()[0][1] == hostname:
            vms_on_this_host.append(inst.keys()[0])
            # vm = VM()
    print("vms_on_this_host: ", vms_on_this_host)

    rui = RUI()  # TODO: separate RUI for every VM
    if vms_on_this_host is not None:
        for domain in vms_on_this_host:
            max_mem, cpu_s = rui.get_vm_info(domain)
            rui.get_utilization(domain)
            # domain_id = hostname + "-" + str(domain)
            vm = VM("domain_id", [max_mem, cpu_s], "demo", node)
            # vm.update_rui(
            #     [rui.cpu_time, rui.memory_used, rui.disk_bytes_read, rui.disk_bytes_written, rui.network_bytes_received,
            #      rui.network_bytes_transmitted])
            vm.update_rui(rui)
            node.update_endowments()


    # Prepare broker sockets
    frontend = context.socket(zmq.ROUTER)
    backend = context.socket(zmq.DEALER)
    frontend.bind("tcp://*:" + own_port)
    # print("frontend_port: ", own_port)
    backend_address = "tcp://" + successor_ip + ":" + successor_port
    # print("backend_address: ", backend_address)
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

            # TODO: extract CRS, check if still same CRS, calculate new ug vector, forward info.
            payload_json = message[-1]
            # header_json = message[:-1]
            # print("payload: ", payload_json)
            # print("header: ", header_json)
            check_update_crs(payload_json)

            # update RUI on all VMs

            new_ug_vector = 0

            backend.send_multipart(message)

        if socks.get(backend) == zmq.POLLIN:
            message = backend.recv_multipart()
            frontend.send_multipart(message)


def check_update_crs(payload_json):
    global crs
    global node
    payload = yaml.safe_load(payload_json)
    new_crs = payload['crs']
    new_crs_hashed = hash(frozenset(new_crs.items()))
    # print("new_crs: ", new_crs)
    # print("new_crs_hashed: ", new_crs_hashed)
    # print("crs.hash_value: ", crs.hash_value)
    if crs.hash_value != new_crs_hashed:
        print("CRS has changed!")
        crs.hash_value = new_crs_hashed
        node.update_global_normalization(new_crs)






def asdf():

    # connect to OpenStack API
    open_stack_connection = IdentityApiConnection()
    user_dict = open_stack_connection.list_users()
    cores, ram = open_stack_connection.get_quotas()
    vm_dict = open_stack_connection.get_all_vms(user_dict)
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
    # node = Node([1/crs[0], 1/crs[1], 1/crs[2], 1/crs[3], 1/crs[4], 1/crs[5]], [nri.cpu, nri.memory, nri.disk_read_bytes, nri.disk_write_bytes, nri.network_receive, nri.network_transmit], user_initial_greediness)
    # print("Node initialized.")

    # filter VMs that are on this host.
    vms_on_this_host = []
    hostname = node.hostname
    for inst in vm_dict:
        if inst.values()[0][1] == hostname:
            vms_on_this_host.append(inst.keys()[0])
    print("vms_on_this_host: ", vms_on_this_host)

    rui = RUI()  # TODO: create new RUI for every VM.
    # domain_id_list = rui.get_domain_id_list()
    if vms_on_this_host is not None:
        for domain in vms_on_this_host:
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

    print("Quota to scalar: ", node.quota_to_scalar([cores, ram]))


def get_successor_from_controller(socket, nri):
    print("sending...")
    json_message = json.dumps({'advertiser': Node.get_public_ip_address(), 'nri': nri})
    socket.send(json_message)

    # print("waiting for response...")
    json_response = socket.recv()
    response = json.loads(json_response)
    ip = response['successor_ip']
    port = response['successor_port']
    own_port = response['requester_port']
    return ip, port, own_port


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
