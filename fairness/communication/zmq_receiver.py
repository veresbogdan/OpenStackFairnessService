# coding=utf-8
import thread
import zmq
import json

from fairness.communication.zmq_sender import Sender


class Receiver:
    nri_sent = False

    def __init__(self):
        context = zmq.Context()
        socket = context.socket(zmq.REP)
        # get own ip here from the manager
        socket.bind("tcp://192.168.1.103:5555")

        while True:
            #  Wait for next request from clients
            message = socket.recv()
            print("Received request: " + message)
            socket.send("Received")

            # start new thread to manage each request
            thread.start_new_thread(Receiver.manage_message, (message,))

    @staticmethod
    def manage_message(message):
        if message is not None:
            json_msj = json.loads(message)

            if 'start' in json_msj:
                print "got start"
                if not Receiver.nri_sent:
                    sender = Sender()
                    sender.send_nri()
                    Receiver.nri_sent = True
                    # send also rui

            if 'nri' in json_msj:
                print "got Nri"
                if not Receiver.nri_sent:
                    sender = Sender()
                    sender.send_nri()
                    Receiver.nri_sent = True
                # do actual stuff here with nri

# just for test purposes (remove this)
Receiver()
