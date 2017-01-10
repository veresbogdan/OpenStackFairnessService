# coding=utf-8
import json
import thread
import time
import zmq
from fairness.node_service.nri import NRI
from fairness.communication.zmq_sender import Sender


class Receiver:
    crs_sent = 0
    interval = 0

    def __init__(self, nri=None):
        self.nri = nri
        self.sender = Sender(nri)

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
            json_msj = json.loads(message)

            # if 'start' in json_msj:
            #     print "got start"
            #     if self.crs_sent < 2:
            #         self.sender.send_crs(self.nri, self.crs_sent)
            #         self.crs_sent += 1
            #     self.interval = int(json_msj['start'])

            if 'crs' in json_msj:
                # if self.crs_sent < 2:
                self.nri.server_crs['crs'] = json_msj['crs']
                self.sender.send_crs(message)
                # self.crs_sent += 1
                # else:
                #     global start
                #     start = time.time()
                #     self.sender.send_greediness(self.nri)

                print 'the crs: '
                print self.nri.server_crs

                # do work here
                # if self.crs_sent == 1:
                #     do work here

            if 'greed' in json_msj:
                self.nri.server_greediness['greed'] = json_msj['greed']

                # if self.interval == 0:
                self.sender.send_greediness(self.nri)
                # else:
                    # measure time again, subtract
                    # end = time.time()
                    # sleep_time = self.interval - (end - start)
                    # time.sleep(sleep_time)
                    # start = time.time()

                    # self.sender.send_greediness(self.nri)

                print 'the list of user greeds: '
                print self.nri.server_greediness


# just for test purposes (remove this)
Receiver(NRI())
