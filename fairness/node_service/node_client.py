# coding=utf-8
import json
import zmq

from fairness.config_parser import MyConfigParser
from fairness.node_service.nri import NRI


class NodeClient:
    context = zmq.Context()
    socket = context.socket(zmq.REQ)

    #  Socket to talk to server
    def __init__(self, nri=None, node=None):
        """
        The initialization of the Node Client. First get the neighbour ip from the controller, then connect with ZMQ to
        the respective neighbour node.
        :param nri:
        :param node:
        """
        self.node = node

        print("Connecting to get the neighbor…")
        config = MyConfigParser()
        controller_ip = config.config_section_map('communication')['controller_ip']
        controller_port = config.config_section_map('communication')['controller_port']
        address = "tcp://" + controller_ip + ":" + controller_port
        self.socket.connect(address)
        json_string = json.dumps({'neighbor': NRI.get_public_ip_address(), 'nri': nri.__dict__})
        self.socket.send(json_string)

        response = self.socket.recv()
        self.socket = self.context.socket(zmq.REQ)

        json_res = json.loads(response)
        if 'neighbor' in json_res:
            address = "tcp://" + json_res['neighbor'] + ":5555"

            print 'The address is: ' + address

            self.socket.connect(address)

    def send_crs(self, message):
        """
        Send the CRS vector to the next node
        :param message: the message to send
        """
        self.socket.send(message)
        self.socket.recv()

    def send_greediness(self, hvn):
        """
        :param nri: the nri class
        """
        # send the result to the next node
        json_string = json.dumps({'hvn': hvn})
        self.socket.send(json_string)
        self.socket.recv()