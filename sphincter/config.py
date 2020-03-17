from configparser import ConfigParser

class SphincterConfigException(Exception):
    pass

class SphincterConfig(object):
    def __init__(self, filename):
        cparser = ConfigParser()
        cparser.read([filename])

        for k, v in cparser.items("Sphincter"):
            self.__dict__[k] = v
