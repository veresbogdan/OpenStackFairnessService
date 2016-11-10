# coding=utf-8
import zmq

from fairness.node.nri import NRI

if __name__ == '__main__':
    context = zmq.Context()

    #  Socket to talk to server
    print("Connecting to server…")
    socket = context.socket(zmq.REQ)
    socket.connect("tcp://" + NRI._get_public_ip_address() + ":5555")

    json_string = "{\"start\":\"10\"}"
    socket.send(json_string)