# coding=utf-8
import json

import zmq

from fairness.nri import NRI

if __name__ == '__main__':
    context = zmq.Context()

    #  Socket to talk to server
    print("Connecting to server…")
    socket = context.socket(zmq.REQ)
    socket.connect("tcp://192.168.1.103:5555")

    nri = NRI()
    json_string = "{\"start\":" + json.dumps(nri.__dict__) + "}"
    socket.send(json_string)