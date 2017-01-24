import MySQLdb as mysql

import numpy as np

from fairness.controller_service.controller_server import ControllerServer
from fairness.drivers.openstack_driver import OpenstackApiConnection
from fairness.node import Node


class ControllerManager:
    def __init__(self):
        self.node = Node()
        self.crs = {}
        # self.ips_list = ['192.168.1.123', '192.168.1.124', '192.168.1.125']

        self.ips_list = []
        tuple_ips = self.get_compute_node_ips()

        for tuple in tuple_ips:
            for res in tuple:
                self.ips_list.append(res)

        print self.ips_list

        ControllerServer(self)

    @staticmethod
    def get_compute_node_ips():
        """
        Get the ips of all compute nodes of openstack from the database
        :return: a tuple of ips
        """
        try:
            password = 'wasserfall'
            db = mysql.connect(user="root", passwd=password, db="nova")
            query = """select host_ip from compute_nodes where deleted=0"""
            db.query(query)
            r = db.use_result()
            results = r.fetch_row(maxrows=0)

            print results

            return results
        except Exception as exp:
            print "Error in accessing the Nova database"
            print exp

    def get_initial_user_vector(self):
        """
        Get from OpenStack API a list with unique users and initialize the user greediness vector to send around.
        CRS needs to be ready for use.
        :return: the initial user vector
        """
        open_stack_connection = OpenstackApiConnection()

        # get users and their's quota
        user_dict = open_stack_connection.list_users()
        vm_dict = open_stack_connection.get_all_vms(user_dict)
        unique_user_list = []
        for item in vm_dict:
            if item.values()[0][0] not in unique_user_list:
                unique_user_list.append(item.values()[0][0])

        # get cores and ram quotas per user.
        initial_user_vector = {}
        quotas_array = np.ones((len(unique_user_list), 6))
        row = 0
        for user in unique_user_list:
            cores, ram = open_stack_connection.get_quotas(user)
            cpu_ratio = self.crs['cpu_bogo'] / self.crs['cpu_num']
            cores_weighted = cores * cpu_ratio
            print(cores)
            print(cpu_ratio)
            print("cores_weighted: ", cores_weighted)
            quotas_array[row] = [cores_weighted, ram, 1, 1, 1, 1]  # Only the first two values are needed. The rest is just filled up with ones (dummy).
            row += 1

        # usm the quotas_array up to a scalar for the initialization of the UGV.
        sum_of_quotas_array = quotas_array.sum(axis=0)  # axis=0 to sum over columns

        crs_array = np.array([self.crs['cpu_bogo'],
                              self.crs['memory'],
                              self.crs['disk_read_bytes'],
                              self.crs['disk_write_bytes'],
                              self.crs['network_receive'],
                              self.crs['network_transmit']])
        row = 0
        self.node.update_global_normalization(self.crs)
        for user in unique_user_list:
            # vec = CRS / Quota of all users * user's Quota /// this is calculated for all 6 resources.
            values_for_initial_user_vector = self.node.global_normalization / np.negative(sum_of_quotas_array) * quotas_array[row]
            initial_user_scalar = values_for_initial_user_vector.sum()
            initial_user_vector[user] = initial_user_scalar
            row += 1
            print(user + "'s, initial_user_scalar: ", initial_user_vector[user])

        return initial_user_vector

ControllerManager()
