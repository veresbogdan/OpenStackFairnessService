from __future__ import print_function

import json
import sys
import threading
import time

import numpy as np
import zmq

from fairness.config_parser import MyConfigParser
from fairness.node import Node
from fairness.node_service.crs import CRS
from fairness.node_service.utils_controller import get_compute_node_ips
from fairness.openstack_driver import IdentityApiConnection

start_ug_event = threading.Event()
own_successor_event = threading.Event()
crs = CRS()
own_successor = 0
successor_port = 65535
initial_user_vector = None
vm_dict = None
open_stack_connection = IdentityApiConnection()


def main():
    """
    This is the main function of the Controller Node. It spawns two child threads:
    One for the node registering server, and one for the communication ring endpoint.
    When everything is ready it starts sending around the UG message with the main thread.
    :return: This code enters in a endless loop sending around the UG message
    """
    global start_ug_event
    global crs
    global own_successor
    global initial_user_vector
    main_context = zmq.Context()

    # prevent that ug-ring starts too early. Too early means: before all nodes advertised their NRI.
    start_ug_event.clear()
    # prevent to connect ug client to (own_successor = 0)
    own_successor_event.clear()

    # spawn a new thread to listen for new incoming nodes
    thread_crs = threading.Thread(target=node_registering)
    thread_crs.daemon = True
    thread_crs.start()

    # spawn a new (server) thread to listen for new incoming ug
    thread_crs = threading.Thread(target=ug_server)
    thread_crs.daemon = True
    thread_crs.start()

    # start the gu-ring client for sending gu + CRS
    client_socket = main_context.socket(zmq.REQ)
    own_successor_event.wait()
    address = "tcp://" + str(own_successor) + ":" + str(successor_port)
    print(address)
    client_socket.connect(address)
    while 1:
        start_ug_event.wait()
        message = {"crs": {"cpu": str(crs.cpu),
                           "memory": str(crs.memory),
                           "disk_read_bytes": str(crs.disk_read),
                           "disk_write_bytes": str(crs.disk_write),
                           "network_receive": str(crs.network_rx),
                           "network_transmit": str(crs.network_tx)},
                   "ug": initial_user_vector}
        print("message sent: ", message)
        json_message = json.dumps(message)
        client_socket.send(json_message)
        ug_response = client_socket.recv()
        print("response: ", ug_response)
        time.sleep(5)

    while 1:
        pass


def node_registering():
    """
    This new thread does:
       - receives the NRI
       - updates the global CRS
       - sends neighbor IP
       - assigns its own successor after all fairness nodes are registered.
       - gives OK for starting the User Greediness (UG) cycles.
    :return: This code enters in a endless loop waiting for new nodes to register.
    """
    global start_ug_event
    global own_successor_event
    global crs
    global own_successor
    global successor_port
    config = MyConfigParser()
    nri_port = config.config_section_map('communication')['nri_port']
    nr_context = zmq.Context()
    nr_socket = nr_context.socket(zmq.REP)
    nr_socket.bind("tcp://*:" + nri_port)

    compute_node_ips = get_compute_node_ips()
    # print("compute_node_ips", compute_node_ips)
    own_ip = Node.get_public_ip_address()
    ip_list = [own_ip]
    ip_list.extend(compute_node_ips)
    print("ip_ist: ", ip_list)

    while 1:
        # Wait for next request from client
        print("waiting for next CRS request from a Node...")
        message = nr_socket.recv()

        start_ug_event.clear()
        # print("Received request: %s" % message)

        # update CRS
        json_res = json.loads(message)
        # print("nri: ", json_res['nri'])
        crs.update_crs(json_res['nri'])
        print("crs.cpu: ", crs.cpu)
        ip_list.remove(json_res['advertiser'])
        successor_ip = ip_list.pop(0)
        ip_list.append(str(json_res['advertiser']))
        # print("ip_list after append: ", ip_list)

        # Send reply back to client (successor_ip, successor_port, requester_port),
        # and set the successor port number in the global variable successor_port for the next requester.
        requester_port = successor_port - 1
        message_1 = {"successor_ip": str(successor_ip), "successor_port": str(successor_port), "requester_port": str(requester_port)}
        successor_port -= 1
        json_message = json.dumps(message_1)
        nr_socket.send(json_message)

        # when all fairness nodes are registered the UG cycle can start.
        if len(ip_list) <= 1:
            init_user_vector()
            own_successor = ip_list.pop(0)
            print("own_successor: ", own_successor)
            start_ug_event.set()
            own_successor_event.set()


def init_user_vector():
    """
    Get from OpenStack API a list with unique users and initialize the user greediness vector to send around.
    :return: None
    """
    # TODO: To get the weighted CPU in initial_user_vector: "crs cpu" / "number of total CPUs in infrastructure". Then multiply the quota value with the result of previous calculation. Ex: 42/6=7 -> 20*7=140
    global crs
    global initial_user_vector
    global vm_dict
    global open_stack_connection

    # get users and their's quota
    if vm_dict is None:
        user_dict = open_stack_connection.list_users()
        vm_dict = open_stack_connection.get_all_vms(user_dict)
    unique_user_list = []
    for item in vm_dict:
        if item.values()[0][0] not in unique_user_list:
            unique_user_list.append(item.values()[0][0])

    # get cores and ram quotas per user.
    initial_user_vector = {}
    quotas_array = np.ones((len(unique_user_list), 6))
    row = 0
    for user in unique_user_list:
        cores, ram = open_stack_connection.get_quotas(user)
        quotas_array[row] = [cores, ram, 1, 1, 1, 1]  # Only the first two values are needed. The rest is just filled up with ones (dummy).
        row += 1

    # fill the crs array and sum it up to a scalar.
    crs_array = np.array([crs.cpu,
                          crs.memory,
                          crs.disk_read,
                          crs.disk_write,
                          crs.network_rx,
                          crs.network_tx])
    sum_of_quotas_array = quotas_array.sum(axis=0)
    row_2 = 0
    for user in unique_user_list:
        values_for_initial_user_vector = crs_array / np.negative(sum_of_quotas_array) * quotas_array[row_2]
        value = values_for_initial_user_vector.sum()
        initial_user_vector[user] = value
        row_2 += 1
        print(user + "'s, initial_user_vector: ", initial_user_vector[user])


def ug_server():
    """
    The User Greediness (UG) message will end up on this server after one complete cycle and this server will
    send back the ACK message.
    :return: This code enters in a endless loop.
    """
    ug_server_context = zmq.Context()
    server_socket = ug_server_context.socket(zmq.REP)
    server_socket.bind("tcp://*:65535")
    while 1:
        updated_ug_message = server_socket.recv()
        # print("updated_ug_message: ", updated_ug_message)
        server_socket.send("UG received.")


if __name__ == '__main__':
    sys.exit(main())
