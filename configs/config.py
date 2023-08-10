import configparser
import ast


class Configs:
    def __init__(self):
        self.config = configparser.ConfigParser()
        self.config.optionxform = str
        self.config_path = None
        self.configs = {}
        self.read_own_configs()
        self.read_configs()

    def read_own_configs(self):
        configs = configparser.ConfigParser()
        configs.optionxform = str
        configs.read("/home/ubuntu/Desktop/Trustee Wallet Analyzer/configs/config.ini")
        self.config_path = ast.literal_eval(configs.get(section='Main', option='ConfigsPath'))

    def read_configs(self):
        self.config.read(self.config_path)
        for section in self.config.sections():
            self.configs[section] = {}
            for option in self.config.options(section):
                self.configs[section][option] = ast.literal_eval(self.config.get(section=section, option=option))
