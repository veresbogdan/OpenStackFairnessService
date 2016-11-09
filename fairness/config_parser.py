import ConfigParser

Config = ConfigParser.ConfigParser()
Config.read('/home/riccardo/sw-projects/PycharmProjects/fairness-service/fairness.ini')


def config_section_map(section):
    dict1 = {}
    options = Config.options(section)
    for option in options:
        try:
            dict1[option] = Config.get(section, option)
            if dict1[option] == -1:
                DebugPrint("skip: %s" % option)
        except:
            print("exception on %s!" % option)
            dict1[option] = None
    return dict1

if Config.has_section('keystone_authtoken'):
    username = config_section_map('keystone_authtoken')['username']
    print username