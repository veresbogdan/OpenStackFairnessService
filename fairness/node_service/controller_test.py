from __future__ import print_function
import sys
import threading
import json
import zmq
import time

from fairness.openstack_driver import IdentityApiConnection
from fairness.node_service.crs import CRS
from fairness.controller.utils_controller import get_compute_node_ips


def main():
    # open_stack_connection = IdentityApiConnection()
    # user_dict = open_stack_connection.list_users()
    # print("user_dict: ", user_dict)

    # spawn a new thread to listen for new incoming nodes
    thread_crs = threading.Thread(target=crs_cycle)
    thread_crs.daemon = True
    thread_crs.start()

    # spawn a new thread to listen for incoming user greediness messages
    # thread_ug = threading.Thread(target=ug_cycle)
    # thread_ug.daemon = True
    # thread_ug.start()

    while 1:
        print("main thread is still running...")
        time.sleep(5)


def crs_cycle():
    """
    the new thread:
       receives the NRI
       updates the global CRS
       sends neighbor IP
    :return:
    """
    context = zmq.Context()
    socket = context.socket(zmq.REP)
    socket.bind("tcp://*:5555")

    compute_node_ips = get_compute_node_ips()
    print("compute_node_ips", compute_node_ips)

    while True:
        #  Wait for next request from client
        print("waiting for next CRS request from a Node...")
        message = socket.recv()
        print("Received request: %s" % message)

        #  update CRS
        json_res = json.loads(message)
        print("nri: ", json_res['nri'])
        crs = CRS()
        crs.update_crs(json_res['nri'])

        #  Send reply back to client
        socket.send("successor IP address")


def ug_cycle():
    """
    the new thread:
       receives UG
       measures time elapsed for current cycle
       starts new UG cycle after defined time.
    :return:
    """
    while 1:
        print("ug_cycle...")
        time.sleep(2)


if __name__ == '__main__':
    sys.exit(main())
