# coding=utf-8
import json
import zmq

from fairness import utils
from fairness.config_parser import MyConfigParser
from fairness.node_service.nri import NRI

class Sender:
    context = zmq.Context()
    socket = context.socket(zmq.REQ)

    #  Socket to talk to server
    def __init__(self, nri=None):
        print("Connecting to get the neighbor…")
        config = MyConfigParser()
        controller_ip = config.config_section_map('keystone_authtoken')['controller_ip']
        address = "tcp://" + controller_ip + ":5555"
        self.socket.connect(address)
        json_string = json.dumps({'neighbor': NRI._get_public_ip_address(), 'nri': nri.__dict__})
        self.socket.send(json_string)

        response = self.socket.recv()
        self.socket = self.context.socket(zmq.REQ)

        json_res = json.loads(response)
        if 'neighbor' in json_res:
            address = "tcp://" + json_res['neighbor'] + ":5555"

            print 'The address is: ' + address

            self.socket.connect(address)

    def send_crs(self, message):
        # own_nri = nri.__dict__

        # if crs_sent < 1:
        # if 'crs' not in nri.server_crs:
        #     nri.server_crs['crs'] = {}
        #
        # nri.server_crs['crs'] = utils.dsum(nri.server_crs['crs'], own_nri)

        # json_string = json.dumps(nri.server_crs)
        self.socket.send(message)
        self.socket.recv()

    def send_greediness(self, nri):
        own_greed = self.get_vm_greediness()

        if 'greed' not in nri.server_greediness:
            nri.server_greediness['greed'] = {}

        nri.server_greediness['greed'] = utils.dsum(nri.server_greediness['greed'], own_greed)
        nri.server_greediness['greed'] = utils.dsum(nri.server_greediness['greed'], nri.old_inverted_greed)
        nri.old_inverted_greed = utils.dminus(own_greed)

        json_string = json.dumps(nri.server_greediness)
        self.socket.send(json_string)
        self.socket.recv()

    # TODO + move
    def get_vm_greediness(self):
        return {'Demo': 5, 'Other': 3, 'Last': 2}