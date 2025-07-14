""" Общие настройки и функции """

import os
from configparser import ConfigParser


CONFIG_FILE = "config.cfg"
DEFAULT_CONF = {
    'Settings': {
        'output_dir': 'windows_data',
        'interval': '1'
    }
}


def load_config():
    """ Функция для заргузки файла конфигурации """
    
    config = ConfigParser()
    if not os.path.exists(CONFIG_FILE):
        config.read_dict(DEFAULT_CONF)

        with open(CONFIG_FILE, 'w') as file:
            config.write(file)
    else:
        config.read(CONFIG_FILE)
    return config
