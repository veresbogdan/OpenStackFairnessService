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
        Sender.socket.connect(address)

    def send_nri(self):
        nri = NRI()
        json_string = "{\"nri\":" + json.dumps(nri.__dict__) + "}"
        Sender.socket.send(json_string)
        reply = Sender.socket.recv()
        print reply
