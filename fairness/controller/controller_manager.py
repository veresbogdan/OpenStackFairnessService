import MySQLdb as mysql

from fairness.openstack_driver import IdentityApiConnection


class ControllerManager:
    def __init__(self):
        # self.ips_list = ['192.168.1.123', '192.168.1.124', '192.168.1.125']

        self.ips_list = []
        tuple_ips = self.get_compute_node_ips()

        for tuple in tuple_ips:
            for res in tuple:
                self.ips_list.append(res)

        print self.ips_list

    @staticmethod
    def get_compute_node_ips():
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
