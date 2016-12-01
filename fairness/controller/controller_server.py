# coding=utf-8
from __future__ import print_function
import json
import zmq

from fairness.controller.utils_controller import UtilsController
from fairness.node import Node
from fairness.node_service.crs import CRS


class Server:
    def __init__(self, manager=None):
        self.manager = manager
        self.host_no = 0
        self.crs = CRS()

        context = zmq.Context()
        socket = context.socket(zmq.REP)
        # get own ip here from the manager
        socket.bind("tcp://" + Node.get_public_ip_address() + ":5555")

        while True:
            #  Wait for next request from clients
            message = socket.recv()
            print("Received request: ", message)
            json_res = json.loads(message)
            print("nri: ", json_res['nri'])

            # take NRI and add to CRS
            self.crs.update_crs(json_res['nri'])

            # socket.send("")


            # start new thread to manage each request
            # self.manage_message(message, socket)

    def manage_message(self, message, socket):
        if message is not None:
            json_msj = json.loads(message)

            if 'neighbor' in json_msj:
                req_ip = json_msj['neighbor']
                ips_list = self.manager.ips_list
                if req_ip in ips_list:
                    index = ips_list.index(req_ip)
                    if index == len(ips_list) - 1:
                        return_message = {'neighbor': ips_list[0]}
                    else:
                        return_message = {'neighbor': ips_list[index + 1]}

                    self.host_no += 1
                    json_string = json.dumps(return_message)
                    socket.send(json_string)

                    if self.host_no == len(ips_list):
                        print('start ring...')
                        self.send_start_message(ips_list[0])

    def send_start_message(self, ip):
        context = zmq.Context()

        #  Socket to talk to server
        print('Connecting to first node…')
        socket = context.socket(zmq.REQ)
        socket.connect("tcp://" + ip + ":5555")

        json_string = "{\"start\":\"10\"}"
        socket.send(json_string)
        socket.recv()


# TODO start the controller service nicely
Server(UtilsController())
