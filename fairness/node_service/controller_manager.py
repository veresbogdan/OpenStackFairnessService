from __future__ import print_function
import sys
import threading
import json
import zmq
import time

from fairness.openstack_driver import IdentityApiConnection
from fairness.node_service.crs import CRS
from fairness.controller.utils_controller import get_compute_node_ips
from fairness.node import Node

crs = CRS()
start_ug_event = threading.Event()
own_successor = 0


def main():

    # spawn a new thread to listen for new incoming nodes
    thread_crs = threading.Thread(target=node_registering)
    thread_crs.daemon = True
    thread_crs.start()

    # TODO: get users and their's quota
    # open_stack_connection = IdentityApiConnection()
    # user_dict = open_stack_connection.list_users()
    # print("user_dict: ", user_dict)
    # cores, ram = open_stack_connection.get_quotas()

    # spawn a new thread to listen for incoming user greediness messages
    thread_ug = threading.Thread(target=ug_cycle)
    thread_ug.daemon = True
    thread_ug.start()

    while 1:
        pass


def node_registering():
    """
    the new thread:
       receives the NRI
       updates the global CRS
       sends neighbor IP
       set semaphore for ug_cycle
    :return:
    """
    global start_ug_event
    global crs
    global own_successor
    nr_context = zmq.Context()
    server_socket = nr_context.socket(zmq.REP)
    server_socket.bind("tcp://*:5555")

    compute_node_ips = get_compute_node_ips()
    # print("compute_node_ips", compute_node_ips)
    own_ip = Node.get_public_ip_address()
    ip_list = [own_ip]
    ip_list.extend(compute_node_ips)
    print("ip_ist: ", ip_list)

    while 1:
        # Wait for next request from client
        print("waiting for next CRS request from a Node...")
        message = server_socket.recv()

        start_ug_event.clear()
        print("Received request: %s" % message)
        # update CRS
        json_res = json.loads(message)
        print("nri: ", json_res['nri'])
        crs.update_crs(json_res['nri'])
        print("crs: ", crs.cpu)
        ip_list.remove(json_res['advertiser'])
        successor_ip = ip_list.pop(0)
        ip_list.append(str(json_res['advertiser']))
        print("ip_list after append: ", ip_list)
        #  Send reply back to client
        server_socket.send(successor_ip)
        if len(ip_list) <= 1:
            own_successor = ip_list.pop(0)
            print("own_successor: ", own_successor)
            start_ug_event.set()


def ug_cycle():
    """
    the new thread:
        send UG+CRS
        receives UG
        measures time elapsed for current cycle
        starts new UG cycle after defined time.
    :return:
    """
    global start_ug_event
    global crs
    global own_successor
    while 1:
        start_ug_event.wait()
        print("ug_cycle...")
        time.sleep(2)
        ug_context = zmq.Context()
        client_socket = ug_context.socket(zmq.REQ)
        address = "tcp://" + own_successor + ":5556"
        client_socket.connect(address)
        print("sending...")
        client_socket.send("hello!")


if __name__ == '__main__':
    sys.exit(main())
