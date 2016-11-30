import sys
import thread

from fairness.controller.controller_manager import ControllerManager


def main():
    controller_managr = ControllerManager
    host_ip_list = controller_managr.ips_list

    # spawn a new thread to listen for new incomming nodes
    thread.start_new_thread(crs_cycle(), args=[])

    # spawn a new thread to listen for incoming user greediness messages
    thread.start_new_thread(ug_cycle(), args=[])

    while 1:
        pass


def crs_cycle():
    """
    the new thread:
       receives the NRI
       updates the global CRS
       sends neighbor IP
    :return:
    """
    pass


def ug_cycle():
    """
    the new thread:
       receives UG
       measures time elapsed for current cycle
       starts new UG cycle after defined time.
    :return:
    """
    pass


if __name__ == '__main__':
    sys.exit(main())
