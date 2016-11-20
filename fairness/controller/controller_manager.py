import MySQLdb as mysql

from fairness.openstack_driver import IdentityApiConnection


class ControllerManager:
    def __init__(self):
        open_stack_conn = IdentityApiConnection()
        # ips_list = [get_compute_node_ips()]
        # replace this
        self.ips_list = ['192.168.1.123', '192.168.1.124', '192.168.1.125']

    def get_compute_node_ips(self):
        try:
            password = 'wasserfall'
            db = mysql.connect(user="root", passwd=password, db="nova")
            query = """select host_ip from compute_nodes where deleted=0"""
            db.query(query)
            r = db.use_result()
            results = r.fetch_row(maxrows=0)
            return results
        except Exception as exp:
            print "Error in accessing the Nova database"
            print exp
