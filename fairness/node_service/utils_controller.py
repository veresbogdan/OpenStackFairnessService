from __future__ import print_function
import MySQLdb as MySQL


def get_compute_node_ips():
    try:
        password = 'wasserfall'
        db = MySQL.connect(user="root", passwd=password, db="nova")
        query = """select host_ip from compute_nodes where deleted=0"""
        db.query(query)
        r = db.use_result()
        # print("r from query: ", r)
        results = r.fetch_row(maxrows=0)
        ips_list = []
        for valor in results:
            for res in valor:
                ips_list.append(res)
        return ips_list
    except Exception as exp:
        print("Error in accessing the Nova database")
        print(exp)
