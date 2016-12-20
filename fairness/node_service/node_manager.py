from __future__ import print_function

import json
import sys

import yaml
import zmq
from fairness.crs import CRS
from fairness.nri import NRI

from fairness.config_parser import MyConfigParser
from fairness.node import Node
from fairness.openstack_driver import IdentityApiConnection
from fairness.rui import RUI
from fairness.virtual_machines import VM
from fairness.virtual_machines import get_vrs

crs = CRS()
node = Node()


def main():
    """
    This is the start script for all Compute Nodes. The whole logic comes together in this function.
    """
    global node
    config = MyConfigParser()
    controller_ip = config.config_section_map('keystone_authtoken')['controller_ip']
    nri_port = config.config_section_map('communication')['nri_port']

    # retrieve NRI for the current node.
    nri = NRI()
    node.set_nri(nri)
    # print("CPU weighted by BogoMIPS: ", nri.cpu_bogo)
    # print("Host memory size in kilobytes: ", nri.memory)
    print("Disk read speed in bytes/s: ", nri.disk_read_bytes)
    # print("Disk write speed in bytes/s: ", nri.disk_write_bytes)
    # print("Theoretical network receive throughput in bytes/s: ", nri.network_receive)
    # print("Theoretical network transmit throughput in bytes/s: ", nri.network_transmit)

    context = zmq.Context()
    # create ZeroMQ Socket to talk to the server
    client_socket = context.socket(zmq.REQ)
    print("Connecting to Controller...")
    address = "tcp://" + controller_ip + ":" + nri_port
    client_socket.connect(address)

    # send NRI and get info from Controller
    successor_ip, successor_port, own_port = get_successor_from_controller(client_socket, nri.__dict__)

    # retreive info for creating VM objects.
    open_stack_connection = IdentityApiConnection()
    user_dict = open_stack_connection.list_users()
    # print("user_dict: ", user_dict)
    # user_dict:  {'4a6383e2a52f434386b2774ae8fe82ac': 'demo', 'bb097255bd524eb59debe189cbb0bd55': 'admin', 'bc39f112d92943bbbde80773ee01c1f1': 'glance', 'e6a534d6987048d8ab30fea4f7f34ca5': 'fairness', 'f387bb59a1454458b4ff8f82d9e51f7a': 'neutron', 'd928bbdff12d45d097ba58fdb90bac3c': 'nova'}
    vms_dict = open_stack_connection.get_all_vms(user_dict)
    print("vms_dict: ", vms_dict)
    # vm_dict:  [{'instance-00000006': ('demo', 'n01')}, {'instance-00000005': ('demo', 'n02')}]

    # filter out VMs that are not on this host and create VM objects for every VM on this host.
    hostname = node.hostname
    for inst in vms_dict:
        if inst.values()[0][1] == hostname:
            for key in inst:
                vm_name = str(key)
            vm_owner = inst.values()[0][0]
            max_mem, cpu_s = get_vrs(vm_name)
            print("parameters for VM creation: ", vm_name, max_mem, cpu_s, vm_owner)
            # the VM is being created next
            rui = RUI()
            rui_list = rui.get_utilization(vm_name)
            vm = VM(vm_name, [max_mem, cpu_s], vm_owner, rui)
            vm.update_rui(rui,
                          [rui_list[0],
                           rui_list[1],
                           rui_list[2],
                           rui_list[3],
                           rui_list[4],
                           rui_list[5]])
            # print("rui_list: ", rui_list)
            node.append_vm_and_update_endowments(vm)

    node.get_greediness_per_user()

    print_items_in_node()

    # Prepare broker sockets for the communication ring
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
    print("Node is ready to receive messages from the ring...")
    while 1:
        socks = dict(poller.poll())

        # the CRS + UGV arrives here.
        if socks.get(frontend) == zmq.POLLIN:
            message = frontend.recv_multipart()
            # print("message: ", message)
            print("got message.")

            payload_json = message[-1]
            # header_json = message[:-1]
            # print("payload: ", payload_json)
            # print("header: ", header_json)
            check_update_crs(payload_json)
            # print("global_normalization in the UG cycle: ", node.global_normalization)

            # for all VMs on this node: get RUI, update RUI
            get_and_update_rui()

            node.get_greediness_per_user()

            print_items_in_node()

            # TODO: calculate new User Greediness vector, forward info.
            new_ug_vector = 0

            backend.send_multipart(message)

        # this if is for the ACK messages that come back from the server.
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


def get_and_update_rui():
    for vm in node.vms:
        rui = vm.rui_obj
        rui_list = rui.get_utilization(vm.vm_name)
        vm.update_rui(rui,
                        [rui_list[0],
                         rui_list[1],
                         rui_list[2],
                         rui_list[3],
                         rui_list[4],
                         rui_list[5]])
        # print("rui_list: ", rui_list)


def print_items_in_node():
    for vm in node.vms:
        print("---------------------------------------------------")
        # print ("vm: ", vm)   #  vm:  <fairness.virtual_machines.VM instance at 0x7fabb7ee7b48>
        # print(type(vm))      #  <type 'instance'>
        # print(vm.__dict__)   #  {'vm_name': 'instance-00000006', 'vrs': array([65536,     1]), 'rui': array([  1.24843562e+03,   1.95080000e+05,   2.06991360e+07,   4.25984000e+05,   2.54716000e+06,   1.14800000e+04]), 'heaviness': 272104.33333333331, 'owner': 'demo', 'endowment': array([  1.19980000e+04,   1.00000000e+00])}
        print("vm.vm_name: ", vm.vm_name)
        # print("vm.rui: ", vm.rui)
        # print("vm.owner: ", vm.owner)
        # print("vm.endowment: ", vm.endowment)
        print("VM Heaviness: ", vm.heaviness)
    # print("Quota to scalar: ", node.quota_to_scalar([cores, ram]))
    # print("node.global_normalization: ", node.global_normalization)
    # print("node.vms length: ", len(node.vms))
    print("node.vms[0].heaviness: ", node.vms[0].heaviness)


if __name__ == '__main__':
    sys.exit(main())
