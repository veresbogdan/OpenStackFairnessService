# coding=utf-8
import zmq
import api
from fairness.nri import NRI
import json


class Sender:
    context = zmq.Context()
    socket = context.socket(zmq.REQ)

    #  Socket to talk to server
    def __init__(self):
        print("Connecting to server…")
        address = "tcp://" + api.next_neighbor_address + ":5555"
        self.socket.connect(address)

    def send_nri(self, nri):
        # if not nri.server_nris.has_key(NRI._get_public_ip_address()):
        fnri = {'nri_' + NRI._get_public_ip_address(): nri.__dict__}

        if not nri.server_nris.__contains__('nri'):
            nris = [fnri]
            nri.server_nris['nri'] = nris
        else:
            nri.server_nris['nri'].append(fnri)

        json_string = json.dumps(nri.server_nris)
        self.socket.send(json_string)
        reply = Sender.socket.recv()
        print reply

