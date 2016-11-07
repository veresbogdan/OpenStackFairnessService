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

            if 'start' in json_msj:
                print "got start"
                if self.nri_sent < 2:
                    sender.send_nri(self.nri)
                    self.nri_sent += 1
                    # send also rui

            if 'nri' in json_msj:
                print "got Nri"
                if self.nri_sent < 2:
                    self.nri.server_nris['nri'] = json_msj['nri']
                    sender.send_nri(self.nri)
                    self.nri_sent += 1

                print 'the list of nris: '
                print self.nri.server_nris
                #do work here


# just for test purposes (remove this)
Receiver(NRI())
