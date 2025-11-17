import configparser
import os
import sys

CONFIG_FILE = 'config.ini'

def get_config_path():
    # Get the directory of the executable
    if getattr(sys, 'frozen', False):
        # The application is frozen
        datadir = os.path.dirname(sys.executable)
    else:
        # The application is not frozen
        datadir = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(datadir, CONFIG_FILE)

def init_config():
    """
    Initializes the configuration file if it doesn't exist.
    """
    config_path = get_config_path()
    if not os.path.exists(config_path):
        config = configparser.ConfigParser()
        config['api_keys'] = {
            'google': '',
            'qwen': '',
            'doubao': ''
        }
        with open(config_path, 'w', encoding='utf-8') as configfile:
            config.write(configfile)
        print(f"Configuration file created at {config_path}. Please fill in your API keys.")

def get_api_key(service_name):
    """
    Reads an API key from the configuration file.
    """
    config_path = get_config_path()
    if not os.path.exists(config_path):
        return None
    
    config = configparser.ConfigParser()
    config.read(config_path, encoding='utf-8')
    return config.get('api_keys', service_name, fallback=None)

def get_available_services():
    """
    Returns a list of services that have an API key.
    """
    config_path = get_config_path()
    if not os.path.exists(config_path):
        return []
        
    config = configparser.ConfigParser()
    config.read(config_path, encoding='utf-8')
    
    available_services = []
    if config.has_section('api_keys'):
        for service, key in config.items('api_keys'):
            if key:
                available_services.append(service)
    return available_services

# For developer-specific settings that are not user-configurable
DEV_CONFIG = {
    "WEBDAV_URL": os.getenv("WEBDAV_URL"),
    "APP_USERNAME": os.getenv("APP_USERNAME"),
    "APP_PASSWORD": os.getenv("APP_PASSWORD")
}
