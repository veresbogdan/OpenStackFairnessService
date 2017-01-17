# coding=utf-8
import json
import thread

import zmq

from fairness.node_service.node_client import NodeClient
from fairness.node_service.nri import NRI
from fairness.config_parser import MyConfigParser


class NodeServer:
    config = MyConfigParser()
    zmq_port = config.config_section_map('communication')['controller_port']

    def __init__(self, nri=None, node=None):
        self.nri = nri
        self.node = node
        self.sender = NodeClient(nri, node)

        context = zmq.Context()
        socket = context.socket(zmq.REP)
        # get own ip here from the manager
        socket.bind("tcp://" + NRI.get_public_ip_address() + ":" + self.zmq_port)

        while True:
            #  Wait for next request from clients
            message = socket.recv()
            print("Received request: " + message)
            socket.send("")

            # start new thread to manage each request
            thread.start_new_thread(self.manage_message, (message,))

    def manage_message(self, message):
        if message is not None:
            json_msj = json.loads(message)

            if 'crs' in json_msj:
                self.nri.server_crs['crs'] = json_msj['crs']

                # TODO check this
                self.node.update_global_normalization(self.nri.server_crs['crs'])
                self.sender.send_crs(message)

                print 'the crs: '
                print self.nri.server_crs

                # do work here

            if 'greed' in json_msj:
                self.nri.server_greediness['greed'] = json_msj['greed']

                self.sender.send_greediness(self.nri)

                print 'the list of user greeds: '
                print self.nri.server_greediness
