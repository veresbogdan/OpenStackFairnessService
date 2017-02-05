# coding=utf-8
import json
import thread

import zmq

from fairness.node_service.node_client import NodeClient
from fairness.node_service.nri import NRI
from fairness.config_parser import MyConfigParser
from fairness.node_service.reallocation_manager import ReallocationManager


class NodeServer:
    config = MyConfigParser()
    zmq_port = config.config_section_map('communication')['controller_port']

    def __init__(self, nri=None, node=None):
        """
        Initialize the node server and start the ZMQ listener
        :param nri: the nri class
        :param node: the node class
        """
        self.node = node
        self.sender = NodeClient(nri, node)
        self.reallocation_manager = ReallocationManager(node)

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
        """
        The method that manages accordingly each received message.
        :param message: the received message
        """
        if message is not None:
            json_msj = json.loads(message)

            if 'crs' in json_msj:
                self.node.forward_crs(json_msj['crs'])

                self.sender.send_crs(message)

                print 'the crs: '
                print self.node.crs_dict

            if 'hvn' in json_msj:
                hvn = self.node.forward_hvn(json_msj['hvn'])

                self.sender.send_greediness(hvn)

                print 'the list of user hvn: '
                print self.node.hvn_dict

                self.reallocation_manager.reallocate()
