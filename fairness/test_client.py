import zmq
import socket

zmq_context = zmq.Context()
successor_node = 'n01'

#  Socket to talk to server
print("Connecting to hello world server...")
zmq_socket = zmq_context.socket(zmq.REQ)
zmq_socket.connect("tcp://" + successor_node + ":5555")

#  Do 10 requests, waiting each time for a response
for request in range(3):
    print("Sending request %s ..." % request)
    zmq_socket.send("Hello")

    #  Get the reply.
    message = zmq_socket.recv()
    print("Received reply %s [ %s ]" % (request, message))
