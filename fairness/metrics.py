# coding=utf-8
import numpy as np
import math
import sys
import warnings

import matplotlib.pyplot as plt


# insight: design function must be applied to greed of VMs and unused quota, otherwise it would have different effects,
# if VM releases all or if it is not instantiated
# insight: TO MENTION IN PAPER


normalizer = 1.0  # must be > 0
#starve_design_parameter = normalizer  # must be > 0,  the smaller it is, the faster the starvation limit decreases
floating_error = 0.00000000001  # used by some functions to catch rounding errors
global_norm = None  # used by some function, do not change

# norm is multiplied by the number of consumers, so the number of consumers does not change the greediness,
# when others consume the same
# norm is divided by the number of resources, so the greediness does not change when there are more resources
# (which are consumed in the same ratio)


def nparray_to_string(npin):
    ret = "["
    for i in npin:
        ret += str(i) + ", "
    ret += "]"
    return ret

######################
#                    #
#      CLASSES       #
#                    #
######################


class GreedinessParameters:
    def __init__(self, dcf=1.):
        assert 0 <= dcf <= 1, \
            'DCF should be at at least -1 and at most 1'
        self.dcf = dcf
        self.discount = 2./(dcf+2)
        self.penalty = 4./(dcf+2)

    def __repr__(self):
        return "$\mathfrak{g}^{%s}$" % (
            ('%.2f' % self.dcf).rstrip('0').rstrip('.')
        )


class GreedinessParameters_alt:
    def __init__(self, discount=1.0, penalty=1.0):
        assert -1 <= discount <= 1, \
            'Discount should be at at least -1 and at most 1'
        assert penalty >= 1, \
            'Penalty should be at least 1'
        self.discount = discount
        self.penalty = penalty

    def __repr__(self):
        return "$G_{%s}^{%s}$" % (
            ('%.2f' % self.discount).rstrip('0').rstrip('.'),
            ('%.2f' % self.penalty).rstrip('0').rstrip('.')
        )


class AllocationMethod:
    def __init__(self, method, starvation_parameter=None, scope=None, dcf=None):

        assert method in {
            'LEON-greed',
            'REAL-greed',
            'SIMP-greed',
            'TARG-greed',
            'LEON-defau',
            'LEON-DomRe',
            'LEON-Asset'
        },\
        "Invalid method code"
        self.method = method

        if method == 'LEON-defau':
            self.scope = None
            self.starvation_parameter = None
            self.greediness_parameters = None
        else:
            if 'LEON' in method:
                assert scope in {'global', 'local'},\
                    ("Scope %s is invalid" % scope)
                self.scope = scope
                if scope == 'global':
                    assert -1 <= starvation_parameter, \
                    'Starve_design_parameter must be at least -1'
                    self.starvation_parameter = starvation_parameter
                else:
                    self.starvation_parameter = None
            else:
                self.scope = None
                assert -1 <= starvation_parameter, \
                'Starve_design_parameter must be at least -1'
                self.starvation_parameter = starvation_parameter

            if 'greed' in method:
                self.greediness_parameters = GreedinessParameters(dcf)
            else:
                self.greediness_parameters = None

    def __repr__(self):
        ret = self.method
        if self.scope is not None:
            ret += "  sco %6s " % self.scope
        else:
            ret += "             "

        if self.starvation_parameter is not None:
            ret += "  stv % .2f " % self.starvation_parameter
        else:
            ret += "            "
        if self.greediness_parameters is not None:
            ret += "  dcf %.2f " % self.greediness_parameters.dcf
#            ret += "  dsc %.2f " % self.greediness_parameters.discount
#            ret += "  pnt %.2f " % self.greediness_parameters.penalty
        else:
            ret += "           "
        return ret #.rstrip()


class VM:

    class UserDummy:
        def __init__(self):
            self.greed = 0
            self.asset = 0
            self.drf = 0

    nr = 1
    user_dummy = UserDummy()

    def __init__(self, demands=None, endow=None, greed=0, name=None):

        assert all(isinstance(i, (int, float)) for i in demands), \
            'First parameter must be a list of integers or floats'

        assert endow is None or isinstance(endow, (list, tuple, np.ndarray)), \
            'Endowment invalid'

        assert ((name is None) or isinstance(name, str)), \
            'Second parameter must be a string'

        assert isinstance(greed, (int, float)), \
            'third parameter must be a number'

        self.request_vector = np.array(demands) * 1.0
        self.receive_vector = np.zeros(len(self.request_vector))
        self.starve_vector = [0.0] * len(self.request_vector)
        if endow is None:
            self.endow_vector = None
        else:
            self.endow_vector = np.array(endow)

        self.request_scalar = None  # helper variable for function getTargetAllocation
        self.receive_scalar = 0  # helper variable for function getTargetAllocation
        self.starve_scalar = 0  # helper variable for function getTargetAllocation
        self.endow_scalar = None

        self.greed = greed
        self.asset = 0.
        self.drf = 0.
        self.value_prev = 0.

        self.owner = VM.user_dummy
        self.host = None

        self.name = name
        if name is None:
            self.name = "VM-" + str(VM.nr)
            VM.nr += 1

    def value_total(self, fairness):
        """returns the sum of the VM's and the VM's owner value, without updating summands before"""
        if "greed" in fairness:
            return self.greed + self.owner.greed
        elif fairness == "LEON-Asset":
            return self.asset + self.owner.asset
        elif fairness == "LEON-DomRe":
            return self.drf + self.owner.drf
        else:
            assert False, "Fairnesscode not found"

    def value_self(self, fairness):
        """returns the VM's value, without updating summands before"""
        if 'greed' in fairness:
            return self.greed
        elif fairness == "LEON-Asset":
            return self.asset
        elif fairness == "LEON-DomRe":
            return self.drf
        else:
            assert False, "Fairnesscode <%s> not found" %fairness

    def __repr__(self):
        receives = list()
        for i in self.receive_vector:
            receives.append("%.2f" % i)
        requests = list()
        for j in self.request_vector:
            requests.append("%.2f" % j)
        starves = list()
        for j in self.starve_vector:
            starves.append("%.2f" % j)
        greed_owner = 0
        asset_owner = 0
        drf_owner = 0
        if self.owner:
            greed_owner = self.owner.greed
            asset_owner = self.owner.asset
            drf_owner = self.owner.drf
        ret = "VM %s\n" % self.name
        ret += "greed: %.3f + %.3f = %.3f (%.3f)\n" % (
            self.greed,
            greed_owner,
            (self.greed + greed_owner),
            self.value_total('greed')
        )
        ret+= "asset: %.3f + %.3f = %.3f (%.3f)\n" % (
            self.asset,
            asset_owner,
            (self.asset + asset_owner),
            self.value_total('LEON-Asset')
        )
        ret += "drf  : %.3f + %.3f = %.3f (%.3f)\n" % (
            self.drf,
            drf_owner,
            (self.drf+ drf_owner),
            self.value_total('LEON-DomRe')
        )
        ret += "gets  " + str(receives) + "\nwants " + str(requests) + "\nstarv " + str(starves) + "\n"
        if self.endow_vector is not None:
            endows = list()
            for j in self.endow_vector:
                endows.append("%.2f" % j)
            ret += "endow " + str(endows) + "\n"
        return ret


class User:
    nr = 1
    endow = np.array([10., 10., 10., 10.])

    def __init__(self, vms=None, endowment=None, name=None):

        assert all(isinstance(vm, VM) for vm in vms), \
            'First parameter must be a list of VMs'
        assert endowment is None or isinstance(endowment, (list, tuple, np.ndarray)), \
            'Endowment invalid'
        assert ((name is None) or isinstance(name, str)), \
            'Third parameter must be a string'

        self.vms = vms
        if endowment is None:
            # If no endowment is specified, use standard endowment
            endowment = User.endow
        self.endows_left = np.array(endowment)
        self.endowment = np.array(endowment)
        for vm in self.vms:
            self.endows_left -= vm.endow_vector
            vm.owner = self
        assert (self.endows_left >= 0).all(), \
            'The VMs endowments exceed the owner\'s endowment\nendows left:' + str(self.endows_left)

        self.greed = 0.
        self.asset = 0.
        self.drf = 0.
        self.drf_alt = 0.

        self.name = name
        if name is None:
            self.name = "U-" + str(User.nr)
        User.nr += 1

    def value(self, fairness):
        """returns the user's value, without updating before"""
        if fairness == "LTgr":
            return self.greed
        elif fairness == "LTas":
            return self.asset
        elif fairness == "LTdr":
            return self.drf
        elif fairness == "LTda":
            return self.drf_alt
        else:
            assert False, "Fairnesscode not found"

    def update_usr(self, norm, greediness_parameters):
        self.drf_alt = 0.
        self.asset = 0.
        self.set_greed_baseline(norm)
        self.greed = self.greed_baseline
        resources = np.zeros(len(self.endows_left))
        for vm in self.vms:
            self.drf_alt += vm.drf
            self.asset += vm.asset
            self.greed += vm.greed
            resources += vm.receive_vector
        self.drf = np.max(resources * norm)

    def set_greed_baseline(self, norm):
        """Calculate the User's credit for the unused quota"""
        self.greed_baseline = - sum(self.endowment * norm)# * discount

    def __repr__(self):
        vm_names = ''
        for vm in self.vms:
            vm_names += vm.name
            vm_names += ", "
        return 'User ' + self.name + " greed: " + str(self.greed) + " owns " + vm_names


class Host:
    nr = 1

    # res = np.array([10.,10.,10.,10.])

    def __init__(self, vms, resources, name=None):
        assert all(isinstance(vm, VM) for vm in vms), \
            'vms parameter must be a list of VMs'
        assert ((name is None) or isinstance(name, str)), \
            'Name parameter must be a string'
        self.resources = np.array(resources)
        self.res_left = np.array(resources)

        for vm in vms:
            self.res_left -= vm.endow_vector
            vm.host = self
        assert (self.res_left >= 0).all(), \
            'The VMs endowments exceed the host resources'

        self.name = name
        self.vms = vms
        if name is None:
            self.name = "H-" + str(Host.nr)
            Host.nr += 1

    def allocate(self, allocation_method, cloud):
        """allocate the resources on this host. The VMs' values are updated (unlike the user's values)"""
        func_ids = {'LTgr', 'LTst', 'LTas', 'LTdr'}
        assert isinstance(allocation_method, AllocationMethod), \
            'invalid function id'

        #if func in {'LTgr', 'LTas', 'LTdr'}:
        get_allocation(allocation_method, self.vms, self.resources, True)
        #if func == 'LTst':
        #    standard_policy(self.vms, self.resources)

#        self.update_vms(cloud.greediness_parameters)
#        # Users cannot be updated here, because they run VMs on different hosts

    def update_vms(self, norm, greediness_parameters):#vms, resources, norm, discount):
        """Update the hosted VMs' values according to their receive vectors"""
        update_vm_objects(self.vms, self.resources, True, greediness_parameters, norm)


class Cloud:
    def __init__(self, hosts, greediness_parameters=GreedinessParameters(), starvation_design=1.0):

        assert all(isinstance(host, Host) for host in hosts), \
            'First parameter must be a list of Hosts'
        self.hosts = hosts

        assert isinstance(greediness_parameters, GreedinessParameters), \
            'Second parameter must be GreedinessParameters'
        self.greediness_parameters = greediness_parameters

        number_resources = len(self.hosts[0].resources)
        vms = list()

        self.resources_total = np.zeros(number_resources)

        for host in hosts:
            host.cloud = self
            vms += host.vms
            assert len(host.resources) == number_resources, \
                'Host resource numbers differ'
            self.resources_total += host.resources

        assert len(vms) == len(set(vms)), \
            'Some VMs were assigned to more than one host'

        users = list()
        for vm in vms:
            users += [vm.owner]
        users = set(users)
        users = list(users)

        users.sort(key=lambda x: x.name)

        self.users = users
        self.vms = vms
        self.norm = np.divide(len(self.users) * normalizer / (1.0 * number_resources), self.resources_total)
        self.is_stable = False

        global global_norm
        global_norm = self.norm

        self.starvation_design = starvation_design
#        global starve_design_parameter
#        starve_design_parameter = starvation_design

        self.consumers = list(self.users) + list(self.vms)
        for user in self.users:
            user.set_greed_baseline(self.norm)

    def cloud_to_string(self):
        """Returns a string, that constitutes a python script to recreate the cloud"""
        ret = \
'''from metrics import VM
from metrics import User
from metrics import Host
from metrics import Cloud
from run_experiment import run_cloud
from run_experiment import init
import os\n
init(os.path.basename(__file__)[:-3])\n
'''
        for i in range(len(self.vms)):
            self.vms[i].tsnr = i
        for j in range(len(self.hosts)):
            self.hosts[j].tsnr = i + j
        for k in range(len(self.users)):
            self.users[k].tsnr = i + j + k

        for vm in self.vms:
            ret += "vm" + \
                   str(vm.tsnr) + \
                   " = VM(" + \
                   nparray_to_string(vm.request_vector) + \
                   ", " + \
                   nparray_to_string(vm.endow_vector) + \
                   ", " + str(vm.greed) + \
                   ", \"" + \
                   vm.name + \
                   "\")\n"
                # Attention, greed may be different, when cloud is run
        ret += "\n"
        for host in self.hosts:
            ret += "host" + \
                   str(host.tsnr) + \
                   " = Host(["
            for vm in host.vms:
                ret += "vm" + str(vm.tsnr) + ", "
            ret += "], " + \
                   nparray_to_string(host.resources) + \
                   ", \"" + \
                   host.name + \
                "\")\n"
        ret += "\n"
        for user in self.users:
            ret += "user" + \
                   str(user.tsnr) + \
                   " = User(["
            for vm in user.vms:
                ret += "vm" + str(vm.tsnr) + ", "
            ret += "], " + \
                   nparray_to_string(user.endowment) + \
                   ", \"" + \
                   user.name + \
                   "\")\n"
        ret += "\nhosts = ["
        for host in self.hosts:
            ret += "host" + \
                   str(host.tsnr) + ", "
        ret += "]\ncloud = Cloud(hosts"
        if self.greediness_parameters.discount != 1.0:
            ret += ", discount = " + str(self.greediness_parameters.discount)
        if self.greediness_parameters.penalty != 1.0:
            ret += ", penalty = " + str(self.greediness_parameters.penalty)
        if self.starvation_design != 1.0:
            ret += ", starvation_design = " + str(self.starvation_design)
        ret += ")\n"
        return ret

    def allocate(self, allocation_method, design_allocate=1.0):

        for vm in self.vms:

            if 'greed' in allocation_method.method:
                vm.value_prev = vm.greed
                vm.greed = 0
            elif allocation_method.method == "LEON-Asset":
                vm.value_prev = vm.asset
                vm.asset = 0
            elif allocation_method.method == "LEON-DomRe":
                vm.value_prev = vm.drf
                vm.drf = 0
#            else:
#                assert False, "Fairnesscode not found"

            vm.receive_vector_old = vm.receive_vector
            vm.receive_vector = np.zeros(len(self.resources_total))

        for host in self.hosts:
            host.allocate(allocation_method, self)

        for user in self.users:
            user.update_usr(self.norm, allocation_method.greediness_parameters)

        self.is_stable = True
        for vm in self.vms:
            if (np.absolute(vm.receive_vector - vm.receive_vector_old) > 0.00001).any():
                self.is_stable = False
#                print vm.name
#                print np.absolute(vm.receive_vector - vm.receive_vector_old)
#                print
            vm.receive_vector = design_allocate * vm.receive_vector + (1 - design_allocate) * vm.receive_vector_old

    def __repr__(self):
        ret = ""
        for user in self.users:
            ret += user.name + " g:" + "%.2f" % user.greed + " vms: "
            for vm in user.vms:
                ret += vm.name + ", "
            ret += "\n"

        for host in self.hosts:
            ret += host.name + " vms: "
            for vm in host.vms:
                ret += vm.name + ", "
            ret += "\n"
        return ret

    def update_all(self, greediness_parameters):
        for host in self.hosts:
            host.update_vms(self.norm, greediness_parameters)
        for user in self.users:
            user.update_usr(self.norm, greediness_parameters)

    def get_jains(self, vector):
        if (vector < 0).any():
            print vector
            return float('-inf')
        if (vector == 0).all():
            return 1.
        vector *= 1.0
        return sum(vector)**2 / (len(vector) * sum(vector**2))

    def jains_greed(self):
        vector = np.empty(len(self.users))
        for i in range(len(self.users)):
            vector[i] = \
                self.users[i].value("LTgr") # +\
                #np.sum(self.users[i].endowment * self.norm) # this was added to make it positive. however, this wont work if users have different quota
        # this could also be moved inside get_jains, however, other metrics dont provide negative values
        if vector.min() < 0:
            vector -= vector.min()
#            print "+++"
#            print vector
        return self.get_jains(vector)

    def jains_asset(self):
        vector = np.empty(len(self.users))
        for i in range(len(self.users)):
            vector[i] = self.users[i].value("LTas")
        return self.get_jains(vector)

    def jains_drf_alt(self):
        # normalize resources a VM receives.
        # for each VM get the maximum of the normalized vector and add it up
        vector = np.empty(len(self.users))
        for i in range(len(self.users)):
            vector[i] = self.users[i].value("LTda")
        return self.get_jains(vector)

    def jains_drf(self):
        # sum resources user receives and then determine dominant share
        vector = np.empty(len(self.users))
        for i in range(len(self.users)):
            vector[i] = self.users[i].value("LTdr")
        return self.get_jains(vector)


######################
#                    #
# INITIALIZE METHODS #
#                    #
######################
def check_and_get_tables(vms, supply, endows=False):
    """Constructs and returns different vectors and matrices from the VM objects handed"""
    # Endowments must be bool (not np.array) because specific endowments would be part of the VM object.
    assert(
        isinstance(vms, (list, tuple))
        and
        all(isinstance(vm, VM) for vm in vms)
    ), \
        'First parameter be sequence of VMs'

    assert(
        isinstance(supply, (list, np.ndarray, tuple))
        and
        all(isinstance(res, (int, float)) for res in supply)
    ), \
        'Second parameter be a sequence of numbers'

    number_resources = len(supply)

    assert isinstance(endows, bool), \
        'third parameter must be bool'

    assert all(len(vm.request_vector) == number_resources for vm in vms), \
        'Request vectors dont have the same length as supply'

    if endows:
        assert all(len(vm.endow_vector) == number_resources for vm in vms), \
            'Endowment vectors dont have length of supply'
    else:
        endowment = np.array(supply) / len(vms)
        for vm in vms:
            if vm.endow_vector is not None:
                warnings.warn('The endowment vector of VM %s is being overwritten.' % vm.name)
            vm.endow_vector = np.array(endowment)

    supply = np.array(supply) * 1.0

    demands = np.empty([len(vms), len(supply)])
    receives = np.empty([len(vms), len(supply)])
    endowments = np.empty([len(vms), len(supply)])

    #     weights = np.zeros(len(VMs))
    #     weights[0] = VMs[0].weight
    for i in range(len(vms)):  # concatenate the endowments vector
    #    temp1 = np.array([vms[i + 1].request_vector]) * 1.0
    #    temp2 = np.array([vms[i + 1].receive_vector]) * 1.0
    #    temp3 = np.array([vms[i + 1].endow_vector]) * 1.0

        demands[i, :] = vms[i].request_vector
        receives[i, :] = vms[i].receive_vector
        endowments[i, :] = vms[i].endow_vector
    demands *= 1.0
    receives *= 1.0
    endowments *= 1.0

    assert (np.sum(endowments, axis=0) <= supply + floating_error).all(), \
        'Endowments exceed supply'

    return {
        'supply': supply,
        'demands': demands,
        'receives': receives,
        'endowments': endowments
    }


def check_and_get_norms(supply, demands, endowments=None):

    assert isinstance(supply, np.ndarray), \
        'First parameter must be np.array'

    assert ((demands is None) or (isinstance(demands, np.ndarray))), \
        'Second parameter must be np.array'

    assert endowments is None or isinstance(endowments, np.ndarray), \
        'Third parameter must be np.array'

    assert len(supply) == demands.shape[1],\
        'Supply and demands must have same length'

    assert (demands >= 0).all(),\
        'Demands cannot be negative'

    if isinstance(endowments, np.ndarray):
        assert endowments.shape == demands.shape,\
            'Demands and endowments must have same shape'
        assert (endowments >= 0).all(),\
            'Endowments cannot be negative'
        assert (np.sum(endowments, axis=0) <= supply + floating_error).all(), \
            'Endowments exceed supply'
    else:
        temp = [supply * 1.0 / demands.shape[0]]  # divide the supply by the number of consumers to get the equal share
        endowments = np.empty(demands.shape)
        for i in range(demands.shape[0]):  # concatenate the supply vector
            endowments[i, :] = np.array(temp)

    local_normalizer = normalizer * demands.shape[0] / (1.0 * len(supply))
    global global_norm
    if global_norm is None:
    # the norm vector serves to account for the quantities of different resources, i.e., to normalize resource amounts
        norm = np.divide(local_normalizer, supply)
    else:
        norm = global_norm

    # np.sum(...) calculates the overall request for each resource,
    # which subsequently is divided by the resources supply to arrive at the scarcity of a resource
    norm_w_scarcity = ((np.sum(demands, axis=0) * 1.0) / supply) * norm
    norm_only_scarc = np.divide(local_normalizer, supply)

    scarce = ((np.sum(demands, axis=0) * 1.0) / supply)
    for i in range(len(norm_only_scarc)):
        norm_only_scarc[i] *= math.floor(scarce[i])
    return {
        'norm': norm,
        'norm_w_scarcity': norm_w_scarcity,
        'norm_only_scarc': norm_only_scarc,
        'endowments': endowments
    }


######################
#                    #
# GREEDINESS METHODS #
#                    #
######################


def update_vm_objects(vms, supply, endows, greediness_parameters, norm=None):
    tables = check_and_get_tables(vms, supply, endows)
    norms = check_and_get_norms(tables['supply'], tables['receives'], tables['endowments'])

    if norm is not None:
        assert (norm == norms['norm']).all(), "Norms are not equal"

    greeds = get_greed(tables['supply'], tables['receives'], norms['norm'], tables['endowments'], greediness_parameters)
    assets = get_asset(tables['supply'], tables['receives'], norms['norm'])
    domres = get_drf(tables['supply'], tables['receives'], norms['norm'])

    for i in range(len(vms)):
        vms[i].asset = assets[i]
        vms[i].drf = domres[i]
        vms[i].greed = greeds[i]
    return vms


def get_greed(supply, utilization, norm=None, endowments=None, greediness_parameters=GreedinessParameters()):
    if norm is None:
        init = check_and_get_norms(supply, utilization, endowments)
        norm = init['norm']
        endowments = init['endowments']
    return greediness_raw(endowments, utilization, norm, greediness_parameters) + np.sum(norm * endowments, axis=1)


def get_asset(supply, utilization, norm=None, endowments=None, greediness_parameters=None):
    if norm is None:
        init = check_and_get_norms(supply, utilization)
        norm = init['norm']
    return np.sum(utilization * norm, axis=1)


def get_drf(supply, utilization, norm=None, endowments=None, greediness_parameters=None):
    if norm is None:
        init = check_and_get_norms(supply, utilization)
        norm = init['norm']
    return np.max(utilization * norm, axis=1)


def get_values(allocation_method, supply, utilization, endowments):
    if allocation_method.method in ('LEON-greed', 'REAL-greed'):
        return get_greed(supply, utilization, None, endowments, allocation_method.greediness_parameters)
    elif allocation_method.method == 'LEON-Asset':
        return get_asset(supply, utilization)
    elif allocation_method.method == 'LEON-DomRe':
        return get_drf(supply, utilization)
    else:
        assert False, 'Code "%s" did not match any metric.' % allocation_method.method


def greediness_raw(endowments, utilization, factor, greediness_parameters):

    def gez(a):
        if a > 0:
            return a * 1.
        return 0.

    def lez(a):
        if a < 0:
            return a * 1.
        return 0.

    def duc(a):
        if a > -1:
            return a * 1.
        return -1.

    def not_zero(a):
        if a != 0:
            return a * 1.
        return -1.

    diff_to_equal_share = utilization - endowments
    maxi = np.vectorize(gez)
    mini = np.vectorize(lez)
    make_at_least_minus_one = np.vectorize(duc)
    make_not_zero = np.vectorize(not_zero)
    pos_dem = maxi(diff_to_equal_share)
    neg_dem = mini(diff_to_equal_share)
    ratio = np.divide(np.sum(pos_dem, axis=0), make_not_zero(np.sum(neg_dem, axis=0)))
#    print "\nratio 1" + str(ratio)
    if greediness_parameters.discount < 0:
        ratio = np.ones(endowments.shape[1])
#        print "ratio 2" + str(ratio)

    return np.sum(
        (greediness_parameters.penalty * pos_dem
         - (greediness_parameters.discount * neg_dem * (make_at_least_minus_one(ratio)))
         ) * factor, axis=1
    )


def greediness_raw_alternative(endowments, utilization, norm, greediness_parameters):

    def gez(a):
        if a > 0:
            return a * 1.
        return 0.

    def lez(a):
        if a < 0:
            return a * 1.
        return 0.

    def duc(a):
        if a > -1:
            return a * 1.
        return -1.

    def not_zero(a):
        if a != 0:
            return a * 1.
        return -1.

    diff_to_equal_share = utilization - endowments
    maxi = np.vectorize(gez)
    mini = np.vectorize(lez)
    make_at_least_minus_one = np.vectorize(duc)
    make_not_zero = np.vectorize(not_zero)
    pos_dem = maxi(diff_to_equal_share)

    neg_dem = mini(diff_to_equal_share)
    dcf = -make_at_least_minus_one(np.divide(np.sum(pos_dem, axis=0), make_not_zero(np.sum(neg_dem, axis=0))))
    beta = 4./(dcf+2)
    gamma = 2./(dcf+2)

#    print
#    print "dcf"
#    print dcf
#    print "beta"
#    print beta
#    print "pen " + str(greediness_parameters.penalty)
#    print "gamma"
#    print gamma
#    print "dsc " + str(greediness_parameters.discount)

    return np.sum(
        (beta * pos_dem
        -
        (-gamma * neg_dem)
        ) * norm, axis=1
    )


def get_assetsWScarcity(supply, utilization, weights = 0):
    init = check_and_get_norms( supply, utilization )
    return np.sum(utilization*init['norm_w_scarcity'], axis=1)


def get_assetsOScarcity(supply, utilization, weights = 0):
    init = check_and_get_norms( supply, utilization )
    return np.sum(utilization*init['norm_only_scarc'], axis=1)


def get_GreedinessWScarcity(supply, utilization, greediness_parameters):
    init = check_and_get_norms(supply, utilization)
    # Compared to the "normal" greediness metric, this metric takes the scarcity of resources into account
    # Therefore each resource request is not only weighted by the normalization factor (depending on the overall amounts of resources) but also by the amount of requests divided by the supply, as calculated here
    return greediness_raw( init['endowments'], utilization, init['norm_w_scarcity'], init['resources'], greediness_parameters )


def get_root_penalty(supply, utilization):
    ret = np.empty(utilization.shape[0])
    for vm in range(utilization.shape[0]):
        assert (utilization[vm, :] <= supply).all(), "A VM receives more than is available of a resource"
        result = 1.0
        for res in range(len(supply)):
            result *= 1.0 - (1.0*utilization[vm, res]) / (supply[res]*1.0)
        ret[vm] = 1.0 - pow(result, 1.0 / len(supply))
    return ret

######################
#                    #
# STARVATION METHODS #
#                    #
######################


def starvation_factors_raw(starvation_parameter, greediness):
    # if starve_design_parameter is <= 0, the starvation factors are chosen statically based on this number
    if starvation_parameter is None:
        return np.zeros(len(greediness))

    assert -1 <= starvation_parameter, \
        'starvation_parameter is %f but should be at least -1' % starvation_parameter

    if starvation_parameter <= 0:
        return np.ones(len(greediness)) * -1.0 * starvation_parameter

    starvation_factors = np.empty(len(greediness))
    for i in range(len(greediness)):
        if greediness[i] <= 0:
            starvation_factors[i] = 1.
        else:
            starvation_factors[i] = (
                math.sqrt(
                    (
                        (greediness[i]/normalizer)**2
                        +
                        starvation_parameter
                    )/starvation_parameter
                )
            ) - (greediness[i]/normalizer)/math.sqrt(starvation_parameter)
    return starvation_factors


######################
#                    #
# ALLOCATION METHODS #
#                    #
######################

def get_allocation(allocation_method, vms, supply, endows=False, nr_resources=0):

    assert isinstance(allocation_method, AllocationMethod), \
        "get_allocation_for_leontief's first parameter instance of AllocationMethod"

    if allocation_method.method != "TARG-greed":
        init = check_and_get_tables(vms, supply, endows)

    if allocation_method.method == "LEON-defau":
        standard_policy(vms, init['supply'], endows)
        return
    elif "LEON" in allocation_method.method:
        get_allocation_leon(allocation_method, vms, init)
    elif allocation_method.method == "REAL-greed":
        get_allocation_realistic(allocation_method, vms, init, endows)
    elif allocation_method.method == "SIMP-greed":
        get_allocation_simple(allocation_method, vms, supply, endows)
    elif allocation_method.method == "TARG-greed":
        get_Target_allocation(allocation_method, vms, supply, endows, None, nr_resources)
    else:
        assert False, "Method code not found!"


def get_allocation_leon(allocation_method, vms, init):

    supply = init['supply']
    demands = init['demands']
    endowments = init['endowments']
    nr_vms = len(vms)
    nr_res = len(supply)

    value_cons_vec = np.empty(nr_vms)
    value_self_vec = np.empty(nr_vms)
    value_prev_vec = np.empty(nr_vms)
    for i in range(nr_vms):
        if allocation_method.scope == 'global':
            value_cons_vec[i] = vms[i].value_total(allocation_method.method)        # owner greed + vm greed
        else:
            value_cons_vec[i] = vms[i].value_self(allocation_method.method)
        value_self_vec[i] = vms[i].value_self(allocation_method.method)            # vm greed (is zero, when called by cloud)
        value_prev_vec[i] = - vms[i].value_prev                    # greediness of VM in round before

    # if there is no scarcity
    if (np.sum(demands, axis=0) <= supply).all():
        allocation_denorm = np.empty([len(vms), len(supply)])
        for i in range(len(vms)):
            allocation_denorm[i, :] = np.array(vms[i].request_vector)
            vms[i].receive_vector = np.array(vms[i].request_vector)
    else:
        # demands_relative contains VM requests relative to the overall supply
        demands_relative = demands / supply

        # demands_DRF_norm contains demands_relative such that the sum of relative demands add up to 1 of each VM
        demands_drf_norm = np.empty(demands.shape)
        for i in range(nr_vms):
            for j in range(nr_res):
                if demands_relative[i, j] == 0:
                    demands_drf_norm[i, j] = 0
                else:
                    demands_drf_norm[i, j] = demands_relative[i, j] / np.sum(demands_relative[i, :])

        starvation_factors = starvation_factors_raw(allocation_method.starvation_parameter, value_cons_vec)
        starvation_limits = np.empty(demands.shape)
        endowments = endowments / supply

        for i in range(nr_vms):
            if np.max(demands_drf_norm[i, :]) > 0:
                with np.errstate(divide='ignore', invalid='ignore'):
                    factor = endowments[i, :] / demands_drf_norm[i, :]
                for j in range(len(factor)):
                    if np.isnan(factor[j]):
                        factor[j] = float('inf')
                factor = np.min(factor)
                starvation_limits[i, :] = starvation_factors[i] * factor * demands_drf_norm[i, :]
                if (starvation_limits[i, :] >= demands_relative[i, :]).all():
                    starvation_limits[i, :] = demands_relative[i, :]
                    # print "starvation reduced"
            else:
                starvation_limits[i, :] = np.zeros(demands.shape[1])
            vms[i].starve_vector = np.array(starvation_limits[i, :])

        # this allocation matrix is converges through the loop to the final allocation
        # initially every VMs gets its starvation limit
        allocation = np.array(starvation_limits)  # np.zeros(demands.shape)

        #     allocation_bu = np.array(starvation_limits)
        x = 0
        y = 0
        target_radius = 0.000000001
        approximator_default = 0.05
        factor = 0.9
        # Next is the fraction of a VM's demand that will be added or removed per loop (change frequently)
        approximator = approximator_default

        # calculate current greediness based on
        # the second parameter is the denormalized allocation (something may be allocated du tue starvation limit)

        values = value_prev_vec + value_cons_vec +\
                get_values(allocation_method, supply, allocation * supply, init['endowments'])
        depleted = np.zeros(nr_res, dtype=bool)

        output = False

        while True:
            while True:
                x += 1
                #print "x: %4d" % x
                if math.fabs(approximator) < target_radius * 0.1:
                    approximator = approximator_default
                    #approximator_default /= 2.
                    y += 1
                    if y == 15:
                        print("terminated due to too many iterations")
                        sys.exit(1)
                if (
                    (
                        approximator < 0
                        and
                        np.max(np.sum(allocation, axis=0) * np.invert(depleted)) < 1
                    )
                    or
                    (
                        approximator > 0
                        and
                        np.max(np.sum(allocation, axis=0) * np.invert(depleted)) > 1
                    )
                ):
                    approximator *= - factor

                if approximator < 0:
                    if output:
                        print ("dec "),
                    allocate_to_user = np.argmax(values)

                    for _ in range(nr_vms):
                        if (allocation[allocate_to_user, :] == starvation_limits[allocate_to_user, :]).all():
                            values[allocate_to_user] = float("-inf")
                            allocate_to_user = np.argmax(values)
                        else:
                            break
                else:
                    if output:
                        print ("inc "),
                    allocate_to_user = np.argmin(values)
                    for _ in range(nr_vms):
                        if (allocation[allocate_to_user] == demands_relative[allocate_to_user, :]).all():
                            values[allocate_to_user] = float("inf")
                            allocate_to_user = np.argmin(values)
                        else:
                            break
                if output:
                    print (allocate_to_user),
                    print ("\t"),
                    print (approximator)

                allocation[allocate_to_user, :] += approximator * demands_drf_norm[allocate_to_user, :]

                if (allocation[allocate_to_user, :] <= starvation_limits[allocate_to_user, :]).all():
                    allocation[allocate_to_user, :] = starvation_limits[allocate_to_user, :]

                if (allocation[allocate_to_user] >= demands_relative[allocate_to_user, :]).all():
                    allocation[allocate_to_user, :] = demands_relative[allocate_to_user, :]

                values = get_values(allocation_method, supply, allocation * supply, init['endowments'])
                values += value_cons_vec + value_prev_vec
                value_min = float("inf")
                value_max = float("-inf")

                for i in range(nr_vms):

                    if (allocation[i, :] < demands_relative[i, :]).any():
                        value_min = min(values[i], value_min)

                    if (allocation[i, :] > starvation_limits[i, :]).any():
                        value_max = max(values[i], value_max)

                if False:
                    #print allocation
                    if approximator < 0:
                        inc = -0.1
                    else:
                        inc = 0.1
                    plt.plot([allocate_to_user], [inc], 'go',markersize=20)
                    plt.axhline(linewidth=2, y=(np.max(np.sum(allocation, axis=0))-0.5), color='y')
                    plt.axis([-0.1, (len(vms)+0.1), -0.51,0.6])
                    ax = plt.gca()
                    ax.set_autoscale_on(False)
                    plt.axhline()
                    plt.axhline(y=0.5, color='r')
                    plt.plot(values, 'ro')
                    ax.set_title(str(np.max(np.sum( allocation, axis=0))))
                    plt.show()

                if output:
                    print ("Max allocated: %.10f\t greed range: %.10f (from %.10f to %.10f)" % (
                        np.max(np.sum(allocation, axis=0)),
                        (value_max - value_min),
                        value_min,
                        value_max))
                    print "target range" + "%.10f" % (target_radius * normalizer)
                    print("allocation")
                    print(allocation)
                    print("________________")
                    print(np.sum(allocation, axis=0))
                    print(np.sum(allocation, axis=0) * np.invert(depleted))
                    if value_max == float("-inf"):
                        print("break1")
                    if (
                        value_max - value_min < target_radius * normalizer
                        and
                        1 - target_radius < np.max(np.sum(allocation, axis=0) * np.invert(depleted)) <= 1
                    ):
                        print("break2")
                    if (
                        value_min == float("inf")
                        and
                        np.max(np.sum(allocation, axis=0) * np.invert(depleted)) <= 1
                    ):
                        print("break3")

                if (
                    value_max == float("-inf")
                    or
                    (
                        value_max - value_min < target_radius * normalizer
                        and
                        1 - target_radius < np.max(np.sum(allocation, axis=0) * np.invert(depleted)) <= 1
                    )
                    or
                    (
                        value_min == float("inf")
                        and
                        np.max(np.sum(allocation, axis=0) * np.invert(depleted)) <= 1
                    )
                ):
                    break

            amount_allocated = np.sum(allocation, axis=0)
            escape = True

            for j in range(nr_res):
                if 1 - target_radius < amount_allocated[j]:
                    #                 if depleted[j] == False:
                    #                     depletion_order.append(j)
                    depleted[j] = True

            starvation_limits = np.array(allocation)
            #print depleted
            for i in range(nr_vms):
            #    print "%s  " % vms[i].name + str(any(demands_relative[i, j] > 0 and depleted[j] for j in range(demands.shape[1])))
                if any(demands_relative[i, j] > 0 and depleted[j] for j in range(demands.shape[1])):
                    demands_relative[i, :] = np.array(allocation[i, :])
                    starvation_limits[i, :] = np.array(allocation[i, :])  # worked already without this line
                else:
                    if not (allocation[i] == demands_relative[i, :]).all():
                        escape = False
            x += 1
            approximator = 1 - np.max(np.sum(allocation, axis=0) * np.invert(depleted)) # approximator_default / x
            if escape:
                break

            #else:
            #    print "reenter"

        if False:
            #     abfangen, dass alle schon zufrieden sind (muss man vielleicht gar nicht)
            while np.min(values) < float("inf"):
                cont = False
                #             print "\n\n\n\n\n"
                print ("npmax : %.20f" % np.max(np.sum(allocation, axis=0)))
                #             print allocation
                #             print "________________"
                #             print np.sum( allocation, axis=0)
                allocate_to_user = np.argmin(values)
                print (allocate_to_user),
                #             print ("Changing user\t"),
                #             print (allocate_to_user)
                values[allocate_to_user] = float("inf")

                vm_still_wants = demands_relative[allocate_to_user, :] - allocation[allocate_to_user, :]
                #             print ("vm demand"),
                #             print demands_relative[allocate_to_user,:]
                #             print ("receives"),
                #             print allocation[allocate_to_user,:]
                #             print ("still wants"),
                #             print vm_still_wants
                if np.max(vm_still_wants) == 0:
                    print("VM happy continue")
                    continue

                still_available = np.ones(allocation.shape[1]) - np.sum(allocation, axis=0)
                #             print ("still available"),
                #             print still_available

                if (still_available >= vm_still_wants).all():
                    allocation[allocate_to_user, :] = np.array(demands_relative[allocate_to_user, :])
                    print("continue 2")
                    continue

                demand_factors = np.zeros(demands.shape[1])
                for i in range(demands.shape[1]):
                    if still_available[i] > 0:
                        demand_factors[i] = vm_still_wants[i] / still_available[i]
                    else:
                        if vm_still_wants[i] > 0:
                            print("continue 1")
                            cont = True
                if cont:
                    continue

                #             print ("demand factors"),
                #             print demand_factors

                scarcest_resource = np.argmax(demand_factors)

                #             print "scarcest resource %d"%scarcest_resource

                available_of_scarcest =\
                    1 - np.sum(allocation[:, scarcest_resource])\
                    + allocation[allocate_to_user, scarcest_resource]
                # np.ones(allocation.shape[1]) - np.sum( np.delete(allocation,allocate_to_user,0), axis=0)

                #             print "consumed of scarcest resoure: %f"%np.sum(allocation[:,scarcest_resource])
                #             print "consumed by current user: %f"%allocation[allocate_to_user,scarcest_resource]
                #             print "available of scarcest resource %d: %f"%(scarcest_resource,available_of_scarcest)

                #             print ("factor of what is currently received"),
                #             print "%.20f"%(allocation[allocate_to_user,0] / demands_relative[ allocate_to_user , 0])
                #             print ("factor should be changed to"),
                #             print (available_of_scarcest / demands_relative[allocate_to_user,scarcest_resource])

                allocation[allocate_to_user, :] = (available_of_scarcest / demands_relative[
                    allocate_to_user, scarcest_resource]) * demands_relative[allocate_to_user, :]
            #             print ("change allocation to"),
            #             print allocation[allocate_to_user,:]
        allocation_denorm = allocation * supply

    values = get_values(allocation_method, supply, allocation_denorm, init['endowments'])

    for i in range(len(vms)):
        vms[i].receive_vector = allocation_denorm[i, :]
        if "greed" in allocation_method.method:
            vms[i].greed = values[i] + value_self_vec[i]
        elif allocation_method.method == 'LEON-Asset':
            vms[i].asset = values[i] + value_self_vec[i]
        elif allocation_method.method == 'LEON-DomRe':
            vms[i].drf = values[i] + value_self_vec[i]
        else:
            assert False, "Fairnesscode not found"
        vms[i].starve_vector *= supply
    return vms


def get_Target_allocation(allocation_method, vms_in, supply, endows=False, norm=None, nr_res=0):

    vms = list(vms_in)
    assert isinstance(endows, bool), \
        "fourth parameter must be bool"
    # check if there is enough for all
    total_request = 0
    total_endows = 0
    for vm in vms:
        assert isinstance(vm.request_scalar, (int, float)) and vm.request_scalar >= 0, \
            "VM request_scalar not set correctly"
        total_request += vm.request_scalar
        if endows:
            assert isinstance(vm.endow_scalar, (int, float)) and vm.endow_scalar >= 0, \
                "VM endow_scalar not set correctly"
            total_endows += vm.endow_scalar
        else:
            assert vm.endow_scalar is None, \
                "supposed to generate endowments but endow_scalar is not None"
            vm.endow_scalar = 1.0 * supply / len(vms)

    assert total_endows <= supply + floating_error, \
        "Endowments of %.20f exceed supply of %.20f" % (total_endows, supply)

    if total_request <= supply:
        alloc = np.empty(len(vms))
        endowments = np.empty(len(vms))
        for i in range(len(vms)):
            vms[i].receive_scalar = vms[i].request_scalar
            alloc[i] = vms[i].receive_scalar
            endowments[i] = vms[i].endow_scalar
        greed = get_greed(
            np.array([supply]),
            np.transpose(np.array([alloc])),
            None,
            np.transpose(np.array([endowments])),
            allocation_method.greediness_parameters
        ) / (1.0 * nr_res)
        for i in range(len(vms)):
            vms[i].greed += greed[i]
        return {'supply_left': supply - total_request}

    # cr stand for currently receiving
    cr_all = []
    cr_exp = []  # exp stands for expensive
    done = []

    if norm is None:
        norm = (normalizer * len(vms_in)/(1.0 * nr_res)) / supply  # Scale of one unit of the resource to be allocated
#    else:
    #    print '---' + str((normalizer * len(vms_in)/(1.0 * nr_res)) / supply)
    #    print "+++" + str(norm)
    # print "Target norm  " + str(norm)

    # calculate starvation factors
    greediness = np.empty(len(vms))
    #     weight = np.zeros(len(VMs))
    for i in range(len(vms)):
        greediness[i] = vms[i].value_total(allocation_method.method)
        vms[i].endow_scalar *= norm
        vms[i].request_scalar *= norm
    starvation_factors = starvation_factors_raw(allocation_method.starvation_parameter, greediness)
    del greediness

    # endow = norm * supply / len(vms)  # Equal-share of the resource that is being allocated for every VM
    supply *= norm
    #print "supply: " + str(supply)

    for i in range(len(vms)):
        # The greediness that is stored here in .turn does not include the greediness for the resource to be allocated.
        # WHen the VM receives exactly its endowment of the reosurce, it results in neutral influence on the greed
        # Accordingly, when this greed is reached (with the baseline), it will be more expensive to allocate to the VM
        vms[i].greed += vms[i].endow_scalar
        # print vms[i].endow_scalar
        vms[i].turn = 1. * vms[i].value_total(allocation_method.method)
        vms[i].greed -= vms[i].endow_scalar * allocation_method.greediness_parameters.discount


        if starvation_factors[i] * vms[i].endow_scalar >= vms[i].request_scalar:
            supply -= vms[i].request_scalar
            vms[i].starve_scalar = vms[i].request_scalar
            vms[i].request_scalar = 0
            vms[i].greed += vms[i].starve_scalar * allocation_method.greediness_parameters.discount
            vms[i].greed_max = None
            vms[i].turn = None
            done.append(vms[i])
            # Because the VM is already happy with receiving its starvation limit or less,
            # it can be moved to list _done_, which contains all VMs that will not receive further resources
        else:
            allocate_to_vm = starvation_factors[i] * vms[i].endow_scalar

            vms[i].greed_max = vms[i].value_total(allocation_method.method)
            if vms[i].request_scalar > vms[i].endow_scalar:
                vms[i].greed_max += (
                    vms[i].endow_scalar * allocation_method.greediness_parameters.discount
                    +
                    (vms[i].request_scalar - vms[i].endow_scalar) * allocation_method.greediness_parameters.penalty
                )
            else:
                vms[i].greed_max += vms[i].request_scalar * allocation_method.greediness_parameters.discount
            supply -= allocate_to_vm
            vms[i].request_scalar -= allocate_to_vm
            vms[i].greed += allocate_to_vm * allocation_method.greediness_parameters.discount
            vms[i].starve_scalar = allocate_to_vm

    for vm in done:
        vms.remove(vm)

    # Sort VMs by greediness and set the baseline to the least greedy VM
    vms.sort(key=lambda x: x.value_total(allocation_method.method))

    # WE DEFINE THE BASELINE OF A VM AS ITS GREEDINESS +
    # WHAT IT IS ALLOCATED OF THE SCARCE RESOURCE,
    # I.E. THE BASELINE IS THE GREEDINESS OF A VM,
    # WHEN ALSO THE REALLOCATED RESOURCE IS TAKEN INTO ACCOUNT

    # baseline of initial greediness +
    # allocationg to which all VM should be raised by allocating them more of the scarce resource

    # As long as VMs want resources and there is supply to be allocated
    iteration = 0
    while vms and supply > 0:
        iteration += 1
        # print "round %d" % iteration
        # print "\tSupply %.2f"%supply
        baseline = vms[0].value_total(allocation_method.method)
        # print "\tbaseline %.2f"%baseline

        next = vms.pop(0)
        cr_all.append(next)

        #print next.turn
        #print baseline
        #print "+++"
        if next.turn > baseline:
            cr_exp.append(next)

        while vms and vms[0].value_total(allocation_method.method) == baseline:
            next = vms.pop(0)
            cr_all.append(next)
            if next.turn >= baseline:
                cr_exp.append(next)

        cr_all.sort(key=lambda x: x.greed_max)
        cr_exp.sort(key=lambda x: x.turn)

        # print "\tcurrently receiving: "
        # for i in cr_all:
        #     print "\t\t%s   gre: %.2f, req:%.2f"%(i.name,i.greed_total(),i.request_scalar)

        while (
            supply > 0
            and
            cr_all
            and
            (
                len(vms) == 0
                or
                (
                    cr_all[0].greed_max
                    <=
                    vms[0].value_total(allocation_method.method)
                )
                or
                (
                    cr_exp
                    and
                    cr_exp[0].turn
                    <=
                    vms[0].value_total(allocation_method.method)
                )
            )
        ):
            if cr_exp and cr_all[0].greed_max > cr_exp[0].turn:
                inc_baseline_to = cr_exp[0].turn
            else:
                inc_baseline_to = cr_all[0].greed_max

            baseline_inc = inc_baseline_to - baseline
            # baselinefactor: wie viel es kostet die baseline zu erhoehen
            baseline_factor = (
                (len(cr_all) - len(cr_exp)) / allocation_method.greediness_parameters.penalty
                +
                len(cr_exp) / allocation_method.greediness_parameters.discount
            )                                                                                                            # <---
#            print "\t\tblf       : " + str(baseline_factor)
#            print "\t\tinc bl to : " + str(inc_baseline_to)
#            print "\t\tbl inc    : " + str(baseline_inc)
#            print "\t\tsupply    : " + str(supply)

            if (
                baseline_inc * baseline_factor > supply                                                                    # <--?
            ):
                baseline += supply / baseline_factor                                                                    # <---
                supply = 0
                # print "\t\tsupply depleted when BL set to " + str(baseline)
            else:
                # print "\t\t  else teil"
                baseline = inc_baseline_to
                supply -= baseline_inc * baseline_factor                                                                # <---
                # print "\t\tbaseline %.2f (+ %.2f), supply: %.2f"%(baseline, baseline_inc,supply)
            while(
                cr_all
                and
                cr_all[0].greed_max == baseline
            ):
                cr_all[0].receive_scalar = cr_all[0].request_scalar
                cr_all[0].greed = baseline - cr_all[0].owner.greed

                # print "\t\t\tBaseline reached %s (moved to done)" %(cr_all[0].name)
                if cr_all[0] in cr_exp:
                    cr_exp.remove(cr_all[0])
                done.append(cr_all.pop(0))

            while cr_exp and cr_exp[0].turn <= baseline:
                cr_exp.pop(0)

        if vms and cr_all:
            # print "reached in round %d" % iteration
            if (
                (vms[0].value_total(allocation_method.method) - baseline)
                *
                (
                    (len(cr_all) - len(cr_exp)) / allocation_method.greediness_parameters.penalty
                    +
                    len(cr_exp) / allocation_method.greediness_parameters.discount
                )                                                                                                        # <---
                <
                supply
            ):  # important that it is not <=
                supply -= (
                    (vms[0].value_total(allocation_method.method) - baseline)
                    *
                    (
                    (len(cr_all) - len(cr_exp)) / allocation_method.greediness_parameters.penalty
                    +
                    len(cr_exp) / allocation_method.greediness_parameters.discount                                                        # <---
                    )
                )
            # baseline = VMs[0].greed
            # above not needed, because "baseline" will be updated any at the beginning of outer loop.
            # it would be needed if the "if" above would be "<=" instead of "<"
            else:
                baseline += (
                    supply
                    /
                    (
                    (len(cr_all) - len(cr_exp)) / allocation_method.greediness_parameters.penalty
                    +
                    len(cr_exp) / allocation_method.greediness_parameters.discount                                                        # <---
                    )
                )
                supply = 0
    # needs to be here (and not in else part of "if vms and cr_all:") because,
    # if part is also fulfilled in case of equality,
    # i.e., supply is then zero and big loop not traversed again
    while cr_all:
        #         print "baseline %f" %baseline
        #         print "Current_greed %f" %cr_all[0].greed

        # cr_all[0].receive_scalar = baseline - cr_all[0].greed_total()
        if cr_all[0].turn < baseline:
            cr_all[0].receive_scalar = (
                cr_all[0].endow_scalar
                -
                cr_all[0].starve_scalar
                +
                (baseline - cr_all[0].turn)/allocation_method.greediness_parameters.penalty                                                # <--?
            )
        else:
            cr_all[0].receive_scalar = (baseline - cr_all[0].value_total(allocation_method.method)) / allocation_method.greediness_parameters.discount        # <---

        #         print cr_all[0].receive_scalar
        cr_all[0].greed = baseline - cr_all[0].owner.greed
        # alternative :
        # cr_all[0].greed += baseline - cr_all[0].greed_total()
        done.append(cr_all.pop(0))

    for vm in vms:
        vm.receive_scalar = 0

    done.extend(vms)
    for i in done:
        i.receive_scalar += i.starve_scalar
        i.receive_scalar /= norm
        i.request_scalar += i.starve_scalar
        i.request_scalar /= norm
        i.starve_scalar /= norm
        i.endow_scalar /= norm
        del i.greed_max
        del i.turn
#        i.greed *= norm
        # next line because receiving one "unit" of the resource is covered by the endowment of the VM

        #i.greed -= normalizer  # * i.weight

#        i.greed_user *= norm

    return {'supply_left': supply}


def get_allocation_realistic(allocation_method, vms, init, endows=False, cloud=None):

    assert len(init['supply']) == 4, \
        "There must be exactly four resources."
#    init = check_and_get_tables(vms, supply, endows)
#    supply = init['supply']

    for vm in vms:
        vm.request_scalar = vm.request_vector[1]
        vm.request_vector[1] = 0
        vm.endow_scalar = vm.endow_vector[1]
        vm.endow_vector[1] = 0

    if cloud is None:
        norm = (normalizer * len(vms)/(4.0)) / init['supply'][1]
    else:
        norm = cloud.norm[1]

    get_Target_allocation(allocation_method, vms, init['supply'][1], endows, norm, 4)
    allocation_method_temp = allocation_method.method
#    allocation_method.method = 'LEON-greed'

    for vm in vms:
        # the greediness is decreased in the next line, because it is increased by get_Target_allocation for the endowment
        # however, get_allocation_leon will also increase the allocation for this
        vm.greed -= vm.endow_scalar * norm


    init['demands'][:, 1] = 0
    get_allocation_leon(allocation_method, vms, init)

    for vm in vms:
        vm.receive_vector[1] = vm.receive_scalar
        vm.request_vector[1] = vm.request_scalar
        vm.endow_vector[1] = vm.endow_scalar
        vm.starve_vector[1] = vm.starve_scalar
#    allocation_method.method = allocation_method_temp

    return vms



def get_allocation_simple(allocation_method, vms, supply, endows, cloud=None):

    init = check_and_get_tables(vms, supply, endows)
    supply = init['supply']
    demands = init['demands']
    total_requests = np.sum(demands, axis=0) * 1.0
    ratio = np.divide(total_requests, supply)

#    temp = np.zeros((len(vms),3))
#    for i in range(len(vms)):
#        temp[i,0] = vms[i].greed
#        temp[i,1] = vms[i].asset
#        temp[i,2] = vms[i].drf

    # the greediness with which VMs arrive is stored in offset
    offset = np.empty(len(vms))
    for i in range(len(vms)):
        offset[i] = vms[i].greed

    # non scarce resources are allocated next.
    # this could also be done in the while loop.
    # however, like this the non-scarce resources are allocated first
    # if it would be done in the while loop,
    # they would be allocated last
    for i in np.transpose(np.argwhere(ratio <= 1))[0]:
        for vm in vms:
            vm.receive_vector[i] = vm.request_vector[i]

    update_vm_objects(vms, supply, True, allocation_method.greediness_parameters)

    for i in range(len(vms)):
        vms[i].greed += offset[i]
    del offset

    resource_to_reallocate = np.argmax(ratio)
    while ratio[resource_to_reallocate] > 1:
        norm = (normalizer * len(vms)/(1.0 * len(supply))) / supply
        for i in range(len(vms)):
            # the greediness is decreased in the next line, because it is increased by get_Target_allocation for the endowment
            # however, update VM objects already increased the greediness accordingly, so it has to be decreased again
            vms[i].greed -= vms[i].endow_vector[resource_to_reallocate] * norm[resource_to_reallocate]
            vms[i].request_scalar = vms[i].request_vector[resource_to_reallocate]
            vms[i].receive_scalar = 0
            vms[i].endow_scalar = vms[i].endow_vector[resource_to_reallocate]

        if cloud is None:
            norm = None
        else:
            #norm = 1./(normalizer * len(cloud.users)/(1.0 * len(cloud.resources_total))) / cloud.resources_total[resource_to_reallocate]
            norm = cloud.norm[resource_to_reallocate]
        get_Target_allocation(allocation_method, list(vms), supply[resource_to_reallocate], True, norm, len(supply))


#        print norm
#        print vms[i].endow_vector[resource_to_reallocate] * norm[resource_to_reallocate]

        for i in range(len(vms)):
            vms[i].receive_vector[resource_to_reallocate] = vms[i].receive_scalar

        ratio[resource_to_reallocate] = 0
        resource_to_reallocate = np.argmax(ratio)

    return vms

def standard_policy(vms, supply, endows = False):

#    init = check_and_get_tables(vms, supply, True)
#    supply = init['supply']

    vms_still_receiving = list(vms)
    allocated_in_total = np.zeros(len(supply))

    for vm in vms:
        vm.receive_vector = np.zeros(len(supply))
        if (vm.request_vector == np.zeros(len(supply))).all():
            vms_still_receiving.remove(vm)
        vm.request_vector *= 1.0
        if endows:
            if np.logical_and(vm.endow_vector == 0, vm.request_vector > 0).any():
                vms_still_receiving.remove(vm)
                vm.help_endow_vector = np.ones(len(supply))
            else:
                assert (vm.endow_vector > 0).all(),\
                    "all endowments must be greater zero %s" % vm
                vm.help_endow_vector = vm.endow_vector
        else:
            vm.help_endow_vector = np.ones(len(supply))

    while vms_still_receiving:

        allocated_during_round = np.zeros(len(supply))
        vms_to_remove_this_round = list()
        supply_for_this_round = supply - allocated_in_total

        endows = np.zeros(len(supply))
        for vm in vms_still_receiving:
            endows += vm.endow_vector
        for vm in vms_still_receiving:
            endow_this_round = (
                (vm.request_vector)/(
                    np.max(endows * vm.request_vector/(supply_for_this_round * vm.help_endow_vector)
            )))
#            print "VM " + vm.name + "'s endow this round " + str(endow_this_round)
            if (vm.receive_vector + endow_this_round >= vm.request_vector).all():
                allocated_during_round += vm.request_vector - vm.receive_vector
                vm.receive_vector = vm.request_vector
                vms_to_remove_this_round.append(vm)
            else:
                vm.receive_vector += endow_this_round
                allocated_during_round += endow_this_round

        for vm in vms_to_remove_this_round:
            vms_still_receiving.remove(vm)
        vms_to_remove_this_round = list()
        allocated_in_total += allocated_during_round
        for vm in vms_still_receiving:
            if np.logical_and((vm.request_vector > 0), ((supply - allocated_in_total) < 0.000001)).any():
                vms_to_remove_this_round.append(vm)
        for vm in vms_to_remove_this_round:
            vms_still_receiving.remove(vm)
    for vm in vms:
        del vm.help_endow_vector

'''
def design_user_greed(user_greed):

    # greediness der individuellen VM muss man nicht raus rechnen,
    #     weil es ja eh viel fluctuation gibt
    #     weil das aus der letzten runde ist, es also konsumiert wurde und so, selbst wenn die VM nun weniger bekommt,
    #     das ja auf die letzte runde keinen einfluss hat

    # VM average does not work because VMs have no clear unit
    # sqrt does not work, because sqrt(x)>x for x < 1
    # log  does not work, because its log(<1) < 0
    result = 1.0 * user_greed
    return result
'''