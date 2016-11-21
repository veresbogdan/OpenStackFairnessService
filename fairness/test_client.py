import zmq
import socket

context = zmq.Context()

#  Socket to talk to server
print("Connecting to hello world server...")
zmq_socket = context.socket(zmq.REQ)
zmq_socket.connect("tcp://"+socket.gethostname()+":5555")

#  Do 10 requests, waiting each time for a response
for request in range(3):
    print("Sending request %s ..." % request)
    zmq_socket.send("Hello")

    #  Get the reply.
    message = zmq_socket.recv()
    print("Received reply %s [ %s ]" % (request, message))
