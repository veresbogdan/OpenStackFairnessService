from fairness.drivers.libvirt_driver import LibvirtConnection


class ReallocationManager:
    def __init__(self, node=None):
        self.node = node
        self.host = self.node.hostname
        self.libvirt = LibvirtConnection()

    def reallocate(self):
        """ Apply priorities for all stored instance heavinesses """
        self._calculate_local_heavinesses()

        if self.node.vms is not None:
            for vm in self.node.vms:
                priority = self.heaviness_to_priority(vm.vm_name, vm.heaviness)

                print vm.vm_name + ': Heaviness: ' + str(vm.heaviness) + ' -> Priority: ' + str(priority)

                self.set_cpu_priority(vm.vm_name, priority)
                self.set_memory_priority(vm.vm_name, priority)
                self.set_disk_priority(vm.vm_name, priority)
                self.set_net_priority(vm.vm_name, priority)

                # TODO check if prioritization worked; save data

    def _calculate_local_heavinesses(self):
        """ Calculate heavinesses for all instances running on the compute host

        The heavinesses of each user are added to the heaviness of an instance
        to result in a user-centric heaviness for each instance:
        heaviness(instance) = heaviness(User) + heaviness(instance)
        """

        for vm in self.node.vms:
            vm.heaviness += self.node.hvn_dict[vm.owner]

    def heaviness_to_priority(self, vm_name, heaviness):
        """ Convert the heaviness of an instance into a priority
        The range for the priority is [-50,50] with -50 being the highest
        priority and 50 being the lowest priority. The conversion takes into
        account that heavinesses < 0 should be prioritized higher by a factor
        of 2.5 compared to heavinesses >= 0

        :param vm_name: Name of the instance
        :type vm_name: str
        :param heaviness: Heaviness to convert from
        :type heaviness: float
        :return: Converted priority
        :rtype: int
        """
        if heaviness >= 0:
            priority = heaviness * 50
            if priority > 50:
                priority = 50
        else:
            priority = heaviness * 50 * 2.5
            if priority < -50:
                priority = -50
        # Eliminate harsh jumps in priorities compared to old priorities
        last_priority = self.node.get_vm(vm_name).last_priority
        self.node.get_vm(vm_name).last_priority = priority
        difference = abs(priority - last_priority) * 0.1
        if priority < last_priority:
            priority = last_priority - difference
        else:
            priority = last_priority + difference

        return int(priority)

    def set_cpu_priority(self, vm_name, priority):
        """Sets the cpu share priority of an instance

        The CPU with the highest shares value gets most resources

        :param vm_name: Name in the form 'instance-0000001a'
        :type vm_name: str
        :param priority: Priority for the CPU in the range [-50,50] with -50 as highest and 50 as lowest priority
        :type priority: int
        """

        domain = self.libvirt.domain_lookup(vm_name)
        cpu_shares = self.convert_priority_range(priority, 1, 100)
        params = domain.schedulerParameters()
        params['cpu_shares'] = long(cpu_shares)

        result = domain.setSchedulerParameters(params)

        return not result

    def set_memory_priority(self, vm_name, priority):
        """Set RAM soft limit of an instance

        It is assured that a minimum soft limit of 10 MiB is guaranteed

        :param vm_name: Name in the form 'instance-0000001a'
        :type vm_name: str
        :param priority: RAM priority in the range [-50,50] with -50 as highest and 50 as lowest priority
        :type priority: int
        """

        domain = self.libvirt.domain_lookup(vm_name)
        total_memory = domain.maxMemory()
        softlimit = self.convert_priority_range(priority, 10240, total_memory)
        result = domain.setMemoryParameters(
            {'soft_limit': int(softlimit)})

        # libvirt returns 0 if successful
        return not result

    def set_disk_priority(self, vm_name, priority):
        """Sets the I/O weight of an instance

        The weight is in the range [100,1000]

        :param instance_name: Name in the form 'instance-0000001a'
        :type instance_name: str
        :param priority: I/O priority in the range [-50,50] with -50 as highest and 50 as lowest priority
        :type priority: int
        """
        domain = self.libvirt.domain_lookup(vm_name)

        io_weight = self.convert_priority_range(priority, 100, 1000)
        params = domain.blkioParameters()
        params['weight'] = io_weight
        result = domain.setBlkioParameters(params)

        return not result

    def set_net_priority(self, vm_name, priority):
        """Sets the network priority of an instance
        """
        # TODO implement
        pass

    @staticmethod
    def convert_priority_range(priority, new_minimum, new_maximum):
        """ Convert a priority from the [-50:50] range to a new range.

        The method makes sure that the output will never exceed or underrun
        the new range even if the input-priority is out of range in relation
        to the old range

        :param priority: Priority to convert
        :type priority: int
        :param new_minimum: The minimum value of the new range
        :type new_minimum: int
        :param new_maximum: The maximum value of the new range
        :type new_maximum: int
        :return: Converted priority
        :rtype: int
                """
        new_range = new_maximum - new_minimum
        new_priority = (((-priority + 50) * new_range) / 100) + new_minimum
        if new_priority < new_minimum:
            return new_minimum
        if new_priority > new_maximum:
            return new_maximum
        return new_priority
