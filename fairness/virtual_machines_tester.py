from __future__ import print_function
from fairness.node import Node
from virtual_machines import VM
from fairness.node_service.nri import NRI

__author__ = 'Patrick'

# define two owners, 0 is their heaviness and will be overwritten later
owners = {"user_a": 0, "user_b": 0}

# initalize a node with two resources, both have a normalization factor of one.
# the nodes NRI is 10 of both resources
node = Node()
nri = NRI()
node.set_nri(nri)
# this VM has VRs (10, 20) and is owned by user_b
vm = VM(1, [10, 20], "user_b", node)
# the VM consumes 10 units of the second resource
vm.update_rui([0, 10, 21, 34, 4, 7])

# this VM has VRs (20, 10) and is owned by user_a
vm = VM(2, [20, 10], "user_a", node)
# the VM consumes 10 units of the first resource
vm.update_rui([10, 0, 4, 8, 12, 23])
print(vm.vm_name)
print(vm.endowment)
print(node.global_normalization)
print(node.nri[:2])                 # this is a node parameter
print(vm.owner)
# print(node.owners)                 # this is a node parameter
print("rui: ", vm.rui)
print(len(node.vms))               # this is a node parameter
print(vm.vrs)

# this must be called everytime the set of VMs on the node changes
# it calculates the VMs endowments based on their VRs and the nodes NRI
node.append_vm_and_update_endowments()

# calculate the greediness of VMs on the node
# will be stored in the heaviness attribute
Node.get_greediness_per_user(node)

# print the VMs heaviness/greediness
for vm in node.vms:
    print(vm.heaviness)

# print the number that has to be deducted from the heaviness of a user, who has a quota of (2,3)
print(node.quota_to_scalar([2, 3]))
