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
        key = 'nri_' + NRI._get_public_ip_address()
        own_nri = {key: nri.__dict__}

        if not nri.server_nris.__contains__('nri'):
            nris = [own_nri]
            nri.server_nris['nri'] = nris
        else:
            if not any(d.get(key, None) is not None for d in nri.server_nris['nri']):
                nri.server_nris['nri'].append(own_nri)

        json_string = json.dumps(nri.server_nris)
        self.socket.send(json_string)
        reply = Sender.socket.recv()
        print reply

