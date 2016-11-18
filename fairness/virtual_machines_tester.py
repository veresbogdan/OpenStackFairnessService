__author__ = 'Patrick'

from virtual_machines import Node
from virtual_machines import VM
from virtual_machines import quota_to_scalar

# define two owners, 0 is their heaviness and will be overwritten later
owners = {"user_a": 0, "user_b": 0}

# initalize a node with two resources, both have a normalization factor of one.
# the nodes NRI is 10 of both resources
Node.init([1, 1, 1, 1, 1, 1], [10, 15, 25, 25, 41, 45], owners)

# this VM has VRs (10, 20) and is owned by user_b
vm = VM(1, [10, 20], "user_b")
# the VM consumes 10 units of the second resource
vm.update_rui([0, 10, 21, 34, 4, 7])

# this VM has VRs (20, 10) and is owned by user_a
vm = VM(2, [20, 10], "user_a")
# the VM consumes 10 units of the first resource
vm.update_rui([10, 0, 4, 8, 12, 23])
print vm.vm_id
print vm.endowment
print vm.global_normalization
print Node.nri[:2]                 # this is a node parameter
print vm.owner
print Node.owners                 # this is a node parameter
print vm.rui
print len(Node.vms)               # this is a node parameter
print vm.vrs

# this must be called everytime the set of VMs on the node changes
# it calculates the VMs endowments based on their VRs and the nodes NRI
Node.update_endowments()

# calculate the greediness of VMs on the node
# will be stored in the heaviness attribute
Node.get_greediness_per_user()

# print the VMs heaviness/greediness
for vm in Node.vms:
    print vm.heaviness

# print the number that has to be deducted from the heaviness of a user, who has a quota of (2,3)
print quota_to_scalar([2,3])
