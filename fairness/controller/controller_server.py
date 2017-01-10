# coding=utf-8
import json
import thread
import time
import zmq

from fairness import utils
from fairness.controller.controller_manager import ControllerManager
from fairness.node_service.nri import NRI


class Server:
    interval = 10
    context = zmq.Context()
    client_socket = context.socket(zmq.REQ)

    def __init__(self, manager=None):
        self.manager = manager
        self.host_no = 0
        self.crs = {}

        server_socket = self.context.socket(zmq.REP)
        # get own ip here from the manager
        server_socket.bind("tcp://" + NRI._get_public_ip_address() + ":5555")

        while True:
            #  Wait for next request from clients
            message = server_socket.recv()
            print("Received request: " + message)
            # socket.send("")

            # start new thread to manage each request
            self.manage_message(message, server_socket)

    def manage_message(self, message, socket):
        if message is not None:
            json_msj = json.loads(message)

            if 'nri' in json_msj:
                self.crs = utils.dsum(self.crs, json_msj['nri'])

            if 'neighbor' in json_msj:
                req_ip = json_msj['neighbor']
                ips_list = self.manager.ips_list
                if req_ip in ips_list:
                    index = ips_list.index(req_ip)

                    # the last node in the node list gets the controller as neighbor
                    if index == len(ips_list) - 1:
                        return_message = {'neighbor': NRI._get_public_ip_address()}
                    else:
                        return_message = {'neighbor': ips_list[index + 1]}

                    self.host_no += 1
                    json_string = json.dumps(return_message)
                    socket.send(json_string)

                    if self.host_no == len(ips_list):
                        print 'send crs...'
                        # the controller gets the first node from the node list as neighbor
                        self.send_crs(ips_list[0])

            if 'crs' in json_msj:
                print 'start grid ring...'

                global start
                start = time.time()

                self.start_greed_ring()

            if 'greed' in json_msj:
                print 'got greed...'

                # measure time again, subtract
                end = time.time()
                sleep_time = self.interval - (end - start)
                time.sleep(sleep_time)
                start = time.time()

                self.client_socket.send(message)
                self.client_socket.recv()


    def send_crs(self, ip):
        #  Socket to talk to server
        print('Connecting to first node…')
        self.client_socket.connect("tcp://" + ip + ":5555")

        json_string = json.dumps({'crs': self.crs})
        self.client_socket.send(json_string)
        self.client_socket.recv()

    def start_greed_ring(self):
        json_string = json.dumps({'greed': {}})
        self.client_socket.send(json_string)
        self.client_socket.recv()


# TODO start the controller service nicely
Server(ControllerManager())
