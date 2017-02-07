import numpy as np

from fairness.user import User


class Controller:
    def __init__(self):
        self.crs_forwarded = False
        self.round_started_at = None
        self.round_duration = -1
        self.hvn_round_count = 0

        self.crs_dict = None

        self.users = dict()

    # This method is called by the controller when receiving the crs_dict
    # This method ensure that the crs_dict is forwarded only once
    def forward_crs(self, crs_dict_in):
        """
        Called by the controller when receiving the crs_dict
        Ensures that the crs_dict is forwarded only once
        :param crs_dict_in:
        :return:
        """
        if not self.crs_forwarded:
            # global crs_vec
            # iter = 0
            # for pr in crs_vec:  # concatenate the endowments vector
            #	crs_vec[iter] = crs_vec[pr]
            #	iter += 1
            #	else:
            for i in range(len(crs_dict_in['vec'])):
                if crs_dict_in['vec'][i] != 0:
                    crs_dict_in['vec'][i] = (1. * len(self.users) / 4) / crs_dict_in['vec'][i]
                else:
                    crs_dict_in['vec'][i] = 0.
            self.crs_dict = dict(crs_dict_in)
            self.crs_forwarded = True

            return dict(crs_dict_in)

    def add_user(self, idnt, vcpu, vram, disk=1, netw=1):
        """
        Has to be called for every user before calling start_hvn_colletion()
        :param idnt: the users unique identifier
        :param vcpu: the user's CPU quota
        :param vram: the user's RAM quota
        :param disk: the user's disk quota
        :param netw: the user's network quota
        :return:
        """
        self.users[idnt] = User(idnt, vcpu, vram, disk, netw)

    def start_hvn_rotation(self):
        """
        Start the heaviness rotation, after all users have been added and the crs has been received successfully
        :param seconds: Minimal duration of heaviness rotation in seconds
        :return:
        """
        assert self.crs_forwarded
        # dictionary with an entry for every user

        hvn_dict = dict()

        sum_of_quotas = np.zeros(4)
        for user in self.users:
            sum_of_quotas += self.users[user].quota
        for i in range(4):
            if sum_of_quotas[i] == 0:
                sum_of_quotas[i] = 1

        for user in self.users:
            hvn_dict[user] = -sum(1.0 * len(self.users) * (self.users[user].quota / sum_of_quotas))/4# * np.array([crs_dict['CPUs'], crs_dict['RAM'], crs_dict['disk'], crs_dict['net']]))

        return hvn_dict
