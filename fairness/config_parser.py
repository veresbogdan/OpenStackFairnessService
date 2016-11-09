import ConfigParser


class MyConfigParser(object):

    config = None

    def __init__(self):
        config = ConfigParser.ConfigParser()
        config.read('/home/riccardo/sw-projects/PycharmProjects/fairness-service/fairness.ini')

    def config_section_map(self, section):
        dict1 = {}
        options = self.config.options(section)
        for option in options:
            try:
                dict1[option] = self.config.get(section, option)
                if dict1[option] == -1:
                    print ("skip: %s" % option)  # this was: DebugPrint
            except:
                print("exception on %s!" % option)
                dict1[option] = None
        return dict1

    # if Config.has_section('keystone_authtoken'):
    #     username = config_section_map('keystone_authtoken')['username']
    #     print username