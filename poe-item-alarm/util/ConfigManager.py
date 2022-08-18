import configparser
import os

class ConfigManager:
    # expects absolute path to where the main exe/script is
    def __init__(self, app_path, config_file):
        self.app_path = app_path

        self.config_file = os.path.join(self.app_path, config_file)
        self.config = configparser.ConfigParser()
        self.config.read(self.config_file)

    def _write(self):
        with open(self.config_file, 'w') as cf:
            self.config.write(cf)
    
    def get_threshold(self):
        return self.config.getfloat('ImageMatch','threshold', fallback=.45)

    def get_block_size(self):
        return self.config.getfloat('App', 'blockSize', fallback=78)

    def get_threaded(self):
        return self.config.getboolean('App', 'threaded', fallback=False)

    def set_block_size(self, block_size):
        if not self.config.has_section('App'):
            self.config.add_section('App')
        self.config.set('App', 'blockSize', str(block_size))
        self._write()