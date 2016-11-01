# coding=utf-8
import thread
import zmq
import json

from fairness.communication.zmq_sender import Sender
from fairness.nri import NRI


class Receiver:
    nri_sent = 0

    def __init__(self, nri=None):
        self.nri = nri

        context = zmq.Context()
        socket = context.socket(zmq.REP)
        # get own ip here from the manager
        socket.bind("tcp://" + NRI._get_public_ip_address() + ":5555")

        while True:
            #  Wait for next request from clients
            message = socket.recv()
            print("Received request: " + message)
            socket.send("Received")

            # start new thread to manage each request
            thread.start_new_thread(self.manage_message, (message,))

    def manage_message(self, message):
        if message is not None:
            sender = Sender()

            json_msj = json.loads(message)

            for key in json_msj.keys():
                if key.__contains__('start'):
                    print "got start"
                    if self.nri_sent < 2:
                        sender.send_nri(self.nri)
                        Receiver.nri_sent += 1
                        # send also rui

                if key.__contains__('nri'):
                    print "got Nri"
                    if self.nri_sent < 2:
                        self.nri.server_nris[key] = json_msj[key]
                        sender.send_nri(self.nri)
                        Receiver.nri_sent += 1

                    print 'the list of nris: '
                    print self.nri.server_nris
                    #do work here


# just for test purposes (remove this)
Receiver(NRI())
