from fairness.drivers.openstack_driver import OpenstackApiConnection
from fairness.node_service.node_server import NodeServer
from fairness.node_service.nri import NRI
from fairness.node import Node
from fairness.node_service.rui import RUI
from fairness.virtual_machines import VM
from fairness.virtual_machines import get_vrs


class NodeManager:
    def __init__(self):
        self.node = Node()
        self.nri = NRI()
        self.node.set_nri(self.nri)

        # retrieve info for creating VM objects.
        open_stack_connection = OpenstackApiConnection()
        user_dict = open_stack_connection.list_users()
        vms_dict = open_stack_connection.get_all_vms(user_dict)
        print("vms_dict: ", vms_dict)

        # filter out VMs that are not on this host and create VM objects for every VM on this host.
        hostname = self.node.hostname
        for inst in vms_dict:
            if inst.values()[0][1] == hostname:
                for key in inst:
                    vm_name = str(key)
                vm_owner = inst.values()[0][0]

                # get VRs
                max_mem, cpu_s = get_vrs(vm_name)
                # TODO: check if it's needed to convert VR's cpu_s with BogoMIPS!

                # create RUI and retrieve data from host
                rui = RUI()
                rui_list = rui.get_utilization(vm_name)

                # create and initialize VMs
                print("All parameters for VM creation, without RUI: ", vm_name, max_mem, cpu_s, vm_owner)
                vm = VM(vm_name, [max_mem, cpu_s], vm_owner, rui)
                vm.update_rui(rui,
                              [rui_list[0],
                               rui_list[1],
                               rui_list[2],
                               rui_list[3],
                               rui_list[4],
                               rui_list[5]])
                # print("rui_list: ", rui_list)

                # this must be called every time the set of VMs on the node changes
                # it calculates the VMs endowments based on their VRs and the nodes NRI
                self.node.append_vm_and_update_endowments(vm)

        # TODO check this is needed here
        self.node.update_greediness_per_vm()

        self.print_items_in_node()

        # start the node server and client
        NodeServer(self.nri, self.node)

    def print_items_in_node(self):
        for vm in self.node.vms:
            print("---------------------------------------------------")
            # print ("vm: ", vm)   #  vm:  <fairness.virtual_machines.VM instance at 0x7fabb7ee7b48>
            # print(type(vm))      #  <type 'instance'>
            # print(vm.__dict__)   #  {'vm_name': 'instance-00000006', 'vrs': array([65536,     1]), 'rui': array([  1.24843562e+03,   1.95080000e+05,   2.06991360e+07,   4.25984000e+05,   2.54716000e+06,   1.14800000e+04]), 'heaviness': 272104.33333333331, 'owner': 'demo', 'endowment': array([  1.19980000e+04,   1.00000000e+00])}
            print("vm.vm_name: ", vm.vm_name)
            # print("vm.rui: ", vm.rui)
            # print("vm.owner: ", vm.owner)
            # print("vm.endowment: ", vm.endowment)
            print("VM Heaviness: ", vm.heaviness)
            # print("Quota to scalar: ", node.quota_to_scalar([cores, ram]))
            # print("node.global_normalization: ", node.global_normalization)
            # print("node.vms length: ", len(node.vms))
            # print("node.vms[0].heaviness: ", node.vms[0].heaviness)

NodeManager()