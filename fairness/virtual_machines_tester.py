__author__ = 'Patrick'

from virtual_machines import Node
from virtual_machines import VM
from virtual_machines import get_greediness_per_user
from virtual_machines import quota_to_scalar

# define two owners, 0 is their heaviness and will be overwritten later
owners = {"user_a": 0, "user_b": 0}

# initalize a node with two resources, both have a normalization factor of one.
# the nodes NRI is 10 of both resources
Node.init([1, 1], [10, 10], owners)

# this VM has VRs (10, 20) and is owned by user_b
vm = VM([10, 20], "user_b")
print vm.endowment
print vm.global_normalization
print vm.nri
print vm.owner
print vm.owners
print vm.rui
print len(vm.vms)
print vm.vrs
# the VM consumes 10 units of the second resource
vm.update_rui([0,10])

# this VM has VRs (20, 10) and is owned by user_a
vm = VM([20, 10], "user_a")
# the VM consumes 10 units of the first resource
vm.update_rui([10, 0])

# this must be called everytime the set of VMs on the node changes
# it calculates the VMs endowments based on their VRs and the nodes NRI
Node.update_endowments()

# calculate the greediness of VMs on the node
# will be stored in the heaviness attribute
get_greediness_per_user()

# print the VMs heaviness/greediness
for vm in VM.vms:
    print vm.heaviness

# print the number that has to be deducted from the heaviness of a user, who has a quota of (2,3)
print quota_to_scalar([2,3])
