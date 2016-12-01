from __future__ import print_function
import sys
import thread

from fairness.controller.utils_controller import UtilsController
from fairness.openstack_driver import IdentityApiConnection


def main():
    open_stack_connection = IdentityApiConnection()
    user_dict = open_stack_connection.list_users()
    print("user_dict: ", user_dict)

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
