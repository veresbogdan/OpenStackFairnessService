# coding=utf-8
import json
import thread
import zmq
import time
from fairness.fairness_node.nri import NRI
from fairness.fairness_node.rui import RUI
from fairness.communication.zmq_sender import Sender


class Receiver:
    nri_sent = 0
    interval = 0

    def __init__(self, nri=None, rui=None):
        self.nri = nri
        self.rui = rui

        context = zmq.Context()
        socket = context.socket(zmq.REP)
        # get own ip here from the manager
        socket.bind("tcp://" + NRI._get_public_ip_address() + ":5555")

        while True:
            #  Wait for next request from clients
            message = socket.recv()
            print("Received request: " + message)
            socket.send("")

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
                self.interval = int(json_msj['start'])

            if 'nri' in json_msj:
                if self.nri_sent < 2:
                    self.nri.server_nris['nri'] = json_msj['nri']
                    sender.send_nri(self.nri)
                    self.nri_sent += 1
                else:
                    global start
                    start = time.time()
                    sender.send_greediness(self.rui)

                print 'the list of nris: '
                print self.nri.server_nris
                #do work here

            if 'greed' in json_msj:
                self.rui.server_greediness['greed'] = json_msj['greed']

                if self.interval == 0:
                    sender.send_greediness(self.rui)
                else:
                    # measure time again, subtract
                    end = time.time()
                    sleep_time = self.interval - (end - start)
                    time.sleep(sleep_time)
                    start = time.time()

                    sender.send_greediness(self.rui)

                print 'the list of greeds: '
                print self.rui.server_greediness

# just for test purposes (remove this)
Receiver(NRI(), RUI())
