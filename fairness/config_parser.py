import ConfigParser
import sys


class MyConfigParser(object):

    config = ConfigParser.ConfigParser()
    config.read(sys.argv[1])
    # config.read('/usr/lib/python2.7/dist-packages/test_fairness_service/fairness-service/fairness.ini')

    def config_section_map(self, section):
        dict1 = {}
        if self.config.has_section(section):
            options = self.config.options(section)
            for option in options:
                try:
                    dict1[option] = self.config.get(section, option)
                    if dict1[option] == -1:
                        print ("skip: %s" % option)  # this was: DebugPrint
                except:
                    print("exception on %s!" % option)
                    dict1[option] = None
        else:
            "Section not found in Config file!"
        return dict1
